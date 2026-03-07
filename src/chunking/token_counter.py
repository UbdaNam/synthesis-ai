"""Deterministic token counting for Stage 3 chunking."""

from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def normalize_text(value: str) -> str:
    """Normalize whitespace before token counting."""

    return " ".join(value.split())


def count_tokens(value: str) -> int:
    """Count tokens with a deterministic lexical strategy."""

    normalized = normalize_text(value)
    if not normalized:
        return 0
    return len(TOKEN_PATTERN.findall(normalized))
