"""Graph state contract for Stage 1 LangGraph entrypoint."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .document_profile import DocumentProfile
from .extracted_document import ExtractedDocument, ExtractionAttemptRecord


class GraphState(BaseModel):
    """Graph boundary type for triage + extraction stages."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    document_profile: DocumentProfile | None = None
    extracted_document: ExtractedDocument | None = None
    extraction_attempts: list[ExtractionAttemptRecord] = Field(default_factory=list)
    extraction_error: str | None = None
    extraction_meta: dict[str, Any] = Field(default_factory=dict)

