"""Graph state contract for triage, extraction, and chunking stages."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .chunk_relationship import ChunkRelationship
from .document_profile import DocumentProfile
from .extracted_document import ExtractedDocument, ExtractionAttemptRecord
from .ldu import LDU


class GraphState(BaseModel):
    """Graph boundary type for triage, extraction, and chunking stages."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    document_profile: DocumentProfile | None = None
    extracted_document: ExtractedDocument | None = None
    extraction_attempts: list[ExtractionAttemptRecord] = Field(default_factory=list)
    extraction_error: str | None = None
    extraction_meta: dict[str, Any] = Field(default_factory=dict)
    chunked_document: list[LDU] = Field(default_factory=list)
    chunk_relationships: list[ChunkRelationship] = Field(default_factory=list)
    chunking_error: str | None = None
    chunking_meta: dict[str, Any] = Field(default_factory=dict)

