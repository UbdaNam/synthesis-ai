"""Deterministic cross-reference detection and resolution for Stage 3."""

from __future__ import annotations

import re

from src.models.chunk_relationship import ChunkRelationship, RelationshipType
from src.models.extracted_document import stable_content_hash


REFERENCE_PATTERNS: tuple[tuple[RelationshipType, re.Pattern[str]], ...] = (
    ("references_table", re.compile(r"\b(?:see|refer to)?\s*Table\s+(\d+)\b", re.IGNORECASE)),
    ("references_figure", re.compile(r"\b(?:see|refer to)?\s*Figure\s+(\d+)\b", re.IGNORECASE)),
    (
        "references_section",
        re.compile(r"\b(?:see|refer to)?\s*Section\s+((?:\d+\.)*\d+)\b", re.IGNORECASE),
    ),
)


def resolve_references(
    *,
    doc_id: str,
    source_chunk_id: str,
    content: str,
    known_targets: dict[str, str],
) -> list[ChunkRelationship]:
    """Resolve explicit references against known chunk labels."""

    relationships: list[ChunkRelationship] = []
    for relationship_type, pattern in REFERENCE_PATTERNS:
        for match in pattern.finditer(content):
            target_number = match.group(1)
            label_prefix = relationship_type.split("_", 1)[1].replace("_", " ").title()
            target_label = f"{label_prefix} {target_number}"
            target_chunk_id = known_targets.get(target_label)
            rel_key = f"{source_chunk_id}:{relationship_type}:{target_label}:{match.start()}"
            relationships.append(
                ChunkRelationship(
                    id=f"rel-{stable_content_hash(rel_key)[:12]}",
                    doc_id=doc_id,
                    source_chunk_id=source_chunk_id,
                    target_chunk_id=target_chunk_id,
                    relationship_type=relationship_type,
                    target_label=target_label,
                    resolved=target_chunk_id is not None,
                    metadata={"match_text": match.group(0), "start_offset": match.start()},
                )
            )
    return relationships
