from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..models.document_profile import (
    EstimatedExtractionCost,
    LanguageSignal,
    LayoutComplexity,
    OriginType,
)


class ProfilingLedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    char_density: list[float]
    image_ratio: list[float]
    layout_signals: dict[str, float]
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language: LanguageSignal
    estimated_extraction_cost: EstimatedExtractionCost
    processing_time: float = Field(ge=0.0)

