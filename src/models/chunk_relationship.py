"""Stage 3 relationship contracts between logical document units."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


RelationshipType = Literal[
    "references_table",
    "references_figure",
    "references_section",
    "belongs_to_section",
    "follows",
]


class ChunkRelationship(BaseModel):
    """Typed relationship between emitted LDUs."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    source_chunk_id: str = Field(min_length=1)
    target_chunk_id: str | None = None
    relationship_type: RelationshipType
    target_label: str | None = None
    resolved: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_resolution(self) -> "ChunkRelationship":
        if self.resolved and not self.target_chunk_id:
            raise ValueError("Resolved relationships require target_chunk_id")
        if not self.resolved and not self.target_label:
            raise ValueError("Unresolved relationships require target_label")
        return self
