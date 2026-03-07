"""Stable Stage 3 content hash generation."""

from __future__ import annotations

import json
from typing import Any

from src.models.extracted_document import stable_content_hash


def generate_ldu_hash(
    *,
    content: str,
    chunk_type: str,
    page_refs: list[int],
    parent_section: str | None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Generate a deterministic hash for an LDU payload."""

    payload = {
        "content": " ".join(content.split()),
        "chunk_type": chunk_type,
        "page_refs": page_refs,
        "parent_section": parent_section,
        "metadata": metadata or {},
    }
    return stable_content_hash(json.dumps(payload, sort_keys=True, ensure_ascii=True))
