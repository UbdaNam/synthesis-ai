"""Stage 5 provenance contracts."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .extracted_document import BoundingBox


class ProvenanceChainItem(BaseModel):
    """Canonical provenance citation for grounded answers and audit results."""

    model_config = ConfigDict(extra="forbid")

    document_name: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box: BoundingBox
    content_hash: str = Field(min_length=1)
    chunk_id: str | None = None
    section_id: str | None = None
    fact_id: str | None = None

    @model_validator(mode="after")
    def validate_traceability(self) -> "ProvenanceChainItem":
        if self.chunk_id is None and self.fact_id is None:
            raise ValueError("Provenance entries must reference a chunk_id or fact_id")
        return self


ProvenanceChain: TypeAlias = list[ProvenanceChainItem]
