FROM python:3.13-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN addgroup --system gradpath && adduser --system --ingroup gradpath gradpath

COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/src apps/api/src
COPY apps/mcp-server/pyproject.toml apps/mcp-server/pyproject.toml
COPY apps/mcp-server/src apps/mcp-server/src

RUN uv sync --locked --no-dev --package gradpath-api

USER gradpath

EXPOSE 8080

CMD ["/app/.venv/bin/uvicorn", "gradpath_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
