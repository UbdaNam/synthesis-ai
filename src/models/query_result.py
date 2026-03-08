"""Stage 5 query request, tool IO, and final result contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .extracted_document import BoundingBox
from .provenance_chain import ProvenanceChainItem


QueryMode = Literal["question_answering", "audit"]
SupportStatus = Literal["supported", "not_found", "unverifiable"]
RetrievalToolName = Literal["pageindex_navigate", "semantic_search", "structured_query"]


class QueryRequest(BaseModel):
    """User query or claim against a processed document."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    user_query: str = Field(min_length=1)
    mode: QueryMode = "question_answering"
    preferred_retrieval_path: RetrievalToolName | None = None
    section_filters: list[str] = Field(default_factory=list)


class NavigationSectionHit(BaseModel):
    """Normalized PageIndex navigation hit."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    score: float = Field(ge=0.0)
    summary: str = ""
    child_section_ids: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_pages(self) -> "NavigationSectionHit":
        if self.page_start > self.page_end:
            raise ValueError("page_start must be less than or equal to page_end")
        return self


class PageIndexNavigationResult(BaseModel):
    """Typed output of the PageIndex navigation tool."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    matched_sections: list[NavigationSectionHit] = Field(default_factory=list)


class SemanticSearchHit(BaseModel):
    """Normalized semantic search result with provenance metadata."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    section_id: str | None = None
    content: str = Field(min_length=1)
    score: float
    page_refs: list[int] = Field(min_length=1)
    bounding_box: BoundingBox
    content_hash: str = Field(min_length=1)
    chunk_type: str = Field(min_length=1)


class SemanticSearchResult(BaseModel):
    """Typed output of semantic retrieval over persisted chunks."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    section_filters: list[str] = Field(default_factory=list)
    hits: list[SemanticSearchHit] = Field(default_factory=list)


class StructuredQueryRow(BaseModel):
    """Normalized SQLite fact query row with provenance."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    fact_name: str = Field(min_length=1)
    fact_value: str = Field(min_length=1)
    value_type: str = Field(min_length=1)
    unit: str | None = None
    period: str | None = None
    source_chunk_id: str = Field(min_length=1)
    document_name: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box: BoundingBox
    content_hash: str = Field(min_length=1)
    section_id: str | None = None
    score: float = 0.0


class StructuredQueryResult(BaseModel):
    """Typed output of SQLite-backed structured fact retrieval."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    sql: str = Field(min_length=1)
    rows: list[StructuredQueryRow] = Field(default_factory=list)


class QueryAnswerDraft(BaseModel):
    """Model-synthesized answer draft keyed to retrieved evidence IDs."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    support_status: SupportStatus
    cited_chunk_ids: list[str] = Field(default_factory=list)
    cited_fact_ids: list[str] = Field(default_factory=list)


class AuditDecisionDraft(BaseModel):
    """Model-synthesized audit classification keyed to retrieved evidence IDs."""

    model_config = ConfigDict(extra="forbid")

    explanation: str = Field(min_length=1)
    support_status: SupportStatus
    cited_chunk_ids: list[str] = Field(default_factory=list)
    cited_fact_ids: list[str] = Field(default_factory=list)


class QueryResult(BaseModel):
    """Final typed answer contract for Stage 5."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    provenance_chain: list[ProvenanceChainItem] = Field(default_factory=list)
    support_status: SupportStatus
    retrieval_path_used: list[RetrievalToolName] = Field(default_factory=list)
    matched_section_ids: list[str] = Field(default_factory=list)
    matched_fact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_supported_results(self) -> "QueryResult":
        if self.support_status == "supported" and not self.provenance_chain:
            raise ValueError("supported results require provenance_chain entries")
        if not self.retrieval_path_used:
            raise ValueError("retrieval_path_used must not be empty")
        if len(set(self.retrieval_path_used)) != len(self.retrieval_path_used):
            raise ValueError("retrieval_path_used must not contain duplicates")
        return self


class AuditResult(BaseModel):
    """Typed result for claim verification."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1)
    support_status: SupportStatus
    explanation: str = Field(min_length=1)
    provenance_chain: list[ProvenanceChainItem] = Field(default_factory=list)
    retrieval_path_used: list[RetrievalToolName] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_audit_result(self) -> "AuditResult":
        if self.support_status == "supported" and not self.provenance_chain:
            raise ValueError("supported audit results require provenance_chain entries")
        if self.support_status != "supported" and not self.explanation:
            raise ValueError("unsupported audit results require explanation")
        return self
