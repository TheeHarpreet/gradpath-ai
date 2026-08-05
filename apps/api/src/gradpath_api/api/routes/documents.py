"""In-memory document extraction and candidate-approved exports."""

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from gradpath_api.application.documents import (
    MAX_UPLOAD_BYTES,
    DocumentProcessingError,
    build_cv_docx,
    build_cv_pdf,
    extract_document_text,
)
from gradpath_api.domain.documents import CvExportRequest, ExtractedDocument

router = APIRouter()


@router.post("/documents/extract", response_model=ExtractedDocument)
async def extract_document(
    file: Annotated[UploadFile, File()],
) -> ExtractedDocument:
    """Return extracted text without retaining the uploaded document."""

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    try:
        text = extract_document_text(file.filename or "upload", content)
    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return ExtractedDocument(
        filename=file.filename or "upload",
        text=text,
        character_count=len(text),
    )


def _download(content: bytes, media_type: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/documents/export/docx")
async def export_docx(payload: CvExportRequest) -> StreamingResponse:
    """Export the exact approved Markdown as an editable A4 DOCX."""

    return _download(
        build_cv_docx(payload.approved_cv_markdown),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        f"{payload.filename}.docx",
    )


@router.post("/documents/export/pdf")
async def export_pdf(payload: CvExportRequest) -> StreamingResponse:
    """Export the exact approved Markdown as a fixed-layout A4 PDF."""

    return _download(
        build_cv_pdf(payload.approved_cv_markdown),
        "application/pdf",
        f"{payload.filename}.pdf",
    )
