from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OriginType(str, Enum):
    NATIVE_DIGITAL = "native_digital"
    SCANNED_IMAGE = "scanned_image"
    MIXED = "mixed"
    FORM_FILLABLE = "form_fillable"


class LayoutComplexity(str, Enum):
    SINGLE_COLUMN = "single_column"
    MULTI_COLUMN = "multi_column"
    TABLE_HEAVY = "table_heavy"
    FIGURE_HEAVY = "figure_heavy"
    MIXED = "mixed"


class DomainHint(str, Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    GENERAL = "general"


class EstimatedExtractionCost(str, Enum):
    FAST_TEXT_SUFFICIENT = "fast_text_sufficient"
    NEEDS_LAYOUT_MODEL = "needs_layout_model"
    NEEDS_VISION_MODEL = "needs_vision_model"


class LanguageSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_count: int = Field(ge=1)
    character_count_per_page: list[int]
    character_density: list[float]
    image_area_ratio: list[float]
    font_metadata_presence: list[bool]
    bounding_box_distribution: dict[str, Any]


class DocumentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language: LanguageSignal
    domain_hint: DomainHint
    estimated_extraction_cost: EstimatedExtractionCost
    analysis_summary: AnalysisSummary
    created_at: str
    deterministic_version: str = Field(min_length=1)

