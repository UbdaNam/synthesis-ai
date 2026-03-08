"""Typed Stage 1 profiling payload."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OriginType = Literal["native_digital", "scanned_image", "mixed", "form_fillable"]
LayoutComplexity = Literal[
    "single_column", "multi_column", "table_heavy", "figure_heavy", "mixed"
]
DomainHint = Literal["financial", "legal", "technical", "medical", "general"]
EstimatedExtractionCost = Literal[
    "fast_text_sufficient", "needs_layout_model", "needs_vision_model"
]


class LanguageSignal(BaseModel):
    """Detected language and confidence."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=2, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)


class DocumentProfile(BaseModel):
    """Deterministic document profile emitted by Stage 1 triage."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language: LanguageSignal
    domain_hint: DomainHint
    estimated_extraction_cost: EstimatedExtractionCost
    deterministic_version: str = Field(min_length=1)

