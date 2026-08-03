"""Contracts for candidate-controlled document import and export."""

from pydantic import Field

from gradpath_api.domain.analysis import ContractModel


class ExtractedDocument(ContractModel):
    """Plain text extracted from an uploaded document without persistence."""

    filename: str
    text: str
    character_count: int = Field(ge=1)


class CvExportRequest(ContractModel):
    """The exact candidate-approved CV content to format for download."""

    approved_cv_markdown: str = Field(min_length=1, max_length=100_000)
    filename: str = Field(
        default="aligned-cv", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _-]{0,79}$"
    )
