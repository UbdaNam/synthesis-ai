"""Base contracts for Stage 2 extraction strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.models.document_profile import DocumentProfile
from src.models.extracted_document import ExtractedDocument, StrategyName


@dataclass(slots=True)
class ExtractionContext:
    """Execution context for a single strategy attempt."""

    doc_id: str
    file_path: str
    document_profile: DocumentProfile
    rules: dict[str, Any]
    attempt_index: int = 1
    budget_spent: float = 0.0


@dataclass(slots=True)
class StrategyResult:
    """Normalized attempt output returned by every strategy."""

    strategy_used: StrategyName
    confidence_score: float
    document: ExtractedDocument | None
    cost_estimate: float
    usage_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseExtractionStrategy(ABC):
    """Shared strategy interface."""

    name: StrategyName

    @abstractmethod
    def extract(self, context: ExtractionContext) -> StrategyResult:
        """Run strategy and return normalized extraction result."""
