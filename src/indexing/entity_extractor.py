"""Deterministic rule-based key entity extraction for Stage 4."""

from __future__ import annotations

import re
from collections.abc import Iterable

from src.models.ldu import LDU


TITLE_ENTITY_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
IDENTIFIER_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9\-]{1,}\b")


class EntityExtractor:
    """Extract key entities with deterministic regex and normalization rules."""

    def __init__(self, stopwords: Iterable[str] | None = None, max_entities: int = 8) -> None:
        self.stopwords = {word.lower() for word in (stopwords or [])}
        self.max_entities = max_entities

    def extract_for_chunks(self, chunks: Iterable[LDU]) -> list[str]:
        scored: dict[str, int] = {}
        for chunk in chunks:
            for candidate in TITLE_ENTITY_RE.findall(chunk.content):
                normalized = " ".join(candidate.strip().split())
                if not normalized or normalized.lower() in self.stopwords:
                    continue
                scored[normalized] = scored.get(normalized, 0) + 1
            for candidate in IDENTIFIER_RE.findall(chunk.content):
                normalized = " ".join(candidate.strip().split())
                if not normalized or normalized.lower() in self.stopwords:
                    continue
                scored[normalized] = scored.get(normalized, 0) + 2
        ranked = sorted(scored.items(), key=lambda item: (-item[1], item[0].lower()))
        return [entity for entity, _ in ranked[: self.max_entities]]
