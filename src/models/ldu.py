"""Stage 3 semantic chunk output contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .chunk_relationship import ChunkRelationship
from .extracted_document import BoundingBox


ChunkType = Literal[
    "section_header",
    "section_text",
    "table",
    "table_segment",
    "figure",
    "numbered_list",
    "list_segment",
]


class LDU(BaseModel):
    """Logical document unit ready for downstream retrieval."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    chunk_type: ChunkType
    page_refs: list[int] = Field(min_length=1)
    bounding_box: BoundingBox
    parent_section: str | None = None
    token_count: int = Field(ge=0)
    content_hash: str = Field(min_length=1)
    relationships: list[ChunkRelationship] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_page_refs(self) -> "LDU":
        if sorted(set(self.page_refs)) != self.page_refs:
            object.__setattr__(self, "page_refs", sorted(set(self.page_refs)))
        return self
