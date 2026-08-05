"""HTTP security boundary: access control, throttling, headers, and safe logs."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict, deque
from hmac import compare_digest
from time import monotonic
from typing import Any
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from gradpath_api.core.config import Settings

logger = logging.getLogger("gradpath.http")
_PUBLIC_PATHS = {"/health/live", "/health/ready", "/api/v1/meta"}


class InMemoryRateLimiter:
    """Bound requests per client and path for one-process demo deployments."""

    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> tuple[bool, int]:
        now = monotonic()
        async with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= now - self._window:
                timestamps.popleft()
            if len(timestamps) >= self._limit:
                retry_after = max(1, int(self._window - (now - timestamps[0])))
                return False, retry_after
            timestamps.append(now)
            return True, 0


class SecurityBoundaryMiddleware(BaseHTTPMiddleware):
    """Apply production-oriented controls without reading sensitive bodies."""

    def __init__(self, app: Any, *, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._limiter = InMemoryRateLimiter(
            limit=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        started = monotonic()
        request_id = self._request_id(request)
        request.state.request_id = request_id
        client = self._client_identifier(request)
        protected = (
            request.url.path not in _PUBLIC_PATHS and request.method != "OPTIONS"
        )

        if protected and not self._authorised(request):
            response: Response = JSONResponse(
                {"detail": "A valid demo access token is required."},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif protected and request.method not in {"GET", "HEAD", "OPTIONS"}:
            allowed, retry_after = await self._limiter.allow(
                f"{client}:{request.method}:{request.url.path}"
            )
            if not allowed:
                response = JSONResponse(
                    {"detail": "Too many requests. Wait before trying again."},
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Cache-Control"] = "no-store"
        self._log_request(request, response, request_id, started)
        return response

    def _authorised(self, request: Request) -> bool:
        expected = self._settings.demo_access_token
        if expected is None:
            return True
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        return scheme.lower() == "bearer" and compare_digest(
            token,
            expected.get_secret_value(),
        )

    def _client_identifier(self, request: Request) -> str:
        if self._settings.trust_proxy_headers:
            forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if forwarded:
                return forwarded
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _request_id(request: Request) -> str:
        supplied = request.headers.get("X-Request-ID", "")
        if supplied and len(supplied) <= 80 and supplied.replace("-", "").isalnum():
            return supplied
        return f"req-{uuid4().hex}"

    @staticmethod
    def _log_request(
        request: Request,
        response: Response,
        request_id: str,
        started: float,
    ) -> None:
        record = {
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((monotonic() - started) * 1000, 2),
        }
        logger.info(json.dumps(record, separators=(",", ":"), sort_keys=True))
