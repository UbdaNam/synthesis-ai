"""Stage 4 PageIndex contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


SUPPORTED_DATA_TYPES = {
    "tables",
    "figures",
    "equations",
    "narrative_text",
    "lists",
}


class PageIndexNode(BaseModel):
    """Hierarchical navigation node derived from Stage 3 LDUs."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    child_sections: list["PageIndexNode"] = Field(default_factory=list)
    key_entities: list[str] = Field(default_factory=list)
    summary: str = ""
    data_types_present: list[str] = Field(default_factory=list)
    parent_section_id: str | None = None
    chunk_ids: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_node(self) -> "PageIndexNode":
        if self.page_start > self.page_end:
            raise ValueError("page_start must be less than or equal to page_end")
        if len(set(self.data_types_present)) != len(self.data_types_present):
            raise ValueError("data_types_present must be unique")
        unsupported = set(self.data_types_present) - SUPPORTED_DATA_TYPES
        if unsupported:
            raise ValueError(f"Unsupported data types present: {sorted(unsupported)}")
        for child in self.child_sections:
            if child.parent_section_id != self.id:
                raise ValueError("Child nodes must reference the current node as parent")
            if child.doc_id != self.doc_id:
                raise ValueError("Child nodes must share the document id")
        return self


class PageIndexDocument(BaseModel):
    """Persisted Stage 4 artifact for one document."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    root_sections: list[PageIndexNode] = Field(default_factory=list)
    section_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    artifact_path: str = ""
    rule_version: str = Field(min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_document(self) -> "PageIndexDocument":
        for node in self.root_sections:
            if node.parent_section_id is not None:
                raise ValueError("Root sections cannot define parent_section_id")
            if node.doc_id != self.doc_id:
                raise ValueError("Root section doc_id must match PageIndexDocument doc_id")
        if self.section_count != len(self.flatten_nodes()):
            raise ValueError("section_count must equal the total number of nodes")
        return self

    def flatten_nodes(self) -> list[PageIndexNode]:
        nodes: list[PageIndexNode] = []

        def _walk(current: PageIndexNode) -> None:
            nodes.append(current)
            for child in current.child_sections:
                _walk(child)

        for root in self.root_sections:
            _walk(root)
        return nodes


class SectionSummaryRequest(BaseModel):
    """Bounded summary request for one section."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    section_id: str = Field(min_length=1)
    section_title: str = Field(min_length=1)
    chunk_ids: list[str] = Field(default_factory=list)
    source_chunks: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_request(self) -> "SectionSummaryRequest":
        if len(self.chunk_ids) != len(self.source_chunks):
            raise ValueError("chunk_ids and source_chunks must align")
        return self


class SectionSummaryResult(BaseModel):
    """Structured summary result for insertion into PageIndex nodes."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source_chunk_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self) -> "SectionSummaryResult":
        sentence_count = len(
            [part for part in self.summary.replace("?", ".").split(".") if part.strip()]
        )
        if sentence_count < 2 or sentence_count > 3:
            raise ValueError("summary must contain 2-3 sentences")
        return self


class SectionCandidate(BaseModel):
    """Deterministic retrieval-preparation candidate for section narrowing."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    score: float
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    matched_terms: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_candidate(self) -> "SectionCandidate":
        if self.page_start > self.page_end:
            raise ValueError("page_start must be less than or equal to page_end")
        return self


PageIndexNode.model_rebuild()
