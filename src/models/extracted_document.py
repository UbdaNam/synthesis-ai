"""Stage 2 normalized extraction payloads and attempt records."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StrategyName = Literal["fast_text", "layout_aware", "vision"]


class BoundingBox(BaseModel):
    """Source-location rectangle."""

    model_config = ConfigDict(extra="forbid")

    x0: float
    y0: float
    x1: float
    y1: float


class TextBlock(BaseModel):
    """Normalized text segment with provenance."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box: BoundingBox
    reading_order: int = Field(ge=0)
    block_type: Literal["heading", "paragraph", "list_item", "caption", "footnote", "other"]
    text: str
    content_hash: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class StructuredTable(BaseModel):
    """Normalized table payload."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box: BoundingBox
    caption: str | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    content_hash: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class FigureBlock(BaseModel):
    """Normalized figure payload."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box: BoundingBox
    caption: str | None = None
    figure_type: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractedDocument(BaseModel):
    """Canonical Stage 2 extraction output for all strategies."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    strategy_used: StrategyName
    confidence_score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    text_blocks: list[TextBlock] = Field(default_factory=list)
    tables: list[StructuredTable] = Field(default_factory=list)
    figures: list[FigureBlock] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_non_empty_content(self) -> "ExtractedDocument":
        if not self.text_blocks and not self.tables and not self.figures:
            raise ValueError("ExtractedDocument must contain at least one content unit")
        return self


class VisionInvocationMetadata(BaseModel):
    """Metadata for multimodal vision attempts."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    prompt_template_version: str = Field(min_length=1)
    handwriting_detected: bool = False
    usage_tokens: int = Field(ge=0)
    estimated_cost: float = Field(ge=0.0)


class ExtractionAttemptRecord(BaseModel):
    """Attempt-level execution contract used in state and logging."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    attempt_index: int = Field(ge=1)
    strategy_used: StrategyName
    confidence_score: float = Field(ge=0.0, le=1.0)
    cost_estimate: float = Field(ge=0.0)
    usage_tokens: int = Field(default=0, ge=0)
    processing_time: float = Field(ge=0.0)
    escalated: bool
    rule_reference: str = Field(min_length=1)
    final_disposition: Literal["accepted", "escalated", "failed_closed"]
    error_reason: str | None = None


class ExtractionLedgerEntry(BaseModel):
    """Line-oriented JSONL observability record."""

    model_config = ConfigDict(extra="allow")

    doc_id: str = Field(min_length=1)
    strategy_used: StrategyName
    confidence_score: float = Field(ge=0.0, le=1.0)
    cost_estimate: float = Field(ge=0.0)
    processing_time: float = Field(ge=0.0)
    escalation_flag: bool
    threshold_rule_reference: str = Field(min_length=1)
    usage_tokens: int = Field(default=0, ge=0)
    budget_cap: float | None = Field(default=None, ge=0.0)
    budget_spent: float | None = Field(default=None, ge=0.0)
    final_disposition: str | None = None
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def stable_content_hash(value: str) -> str:
    """Compute deterministic SHA-256 hash for content provenance."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
