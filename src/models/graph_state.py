"""Graph state contract for triage, extraction, and chunking stages."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .chunk_relationship import ChunkRelationship
from .document_profile import DocumentProfile
from .extracted_document import ExtractedDocument, ExtractionAttemptRecord
from .ldu import LDU
from .page_index import PageIndexDocument, SectionCandidate
from .query_result import (
    PageIndexNavigationResult,
    QueryRequest,
    QueryResult,
    SemanticSearchHit,
    StructuredQueryRow,
)


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
    page_index: PageIndexDocument | None = None
    page_index_path: str | None = None
    section_candidates: list[SectionCandidate] = Field(default_factory=list)
    indexing_error: str | None = None
    indexing_meta: dict[str, Any] = Field(default_factory=dict)
    query_request: QueryRequest | None = None
    query_result: QueryResult | None = None
    query_messages: list[dict[str, Any]] = Field(default_factory=list)
    navigation_candidates: list[PageIndexNavigationResult] = Field(default_factory=list)
    semantic_hits: list[SemanticSearchHit] = Field(default_factory=list)
    structured_rows: list[StructuredQueryRow] = Field(default_factory=list)
    query_error: str | None = None
    query_meta: dict[str, Any] = Field(default_factory=dict)

