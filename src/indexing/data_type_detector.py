"""Deterministic data-type detection for PageIndex sections."""

from __future__ import annotations

from collections.abc import Iterable

from src.models.ldu import LDU


CHUNK_TYPE_TO_DATA_TYPE = {
    "section_header": "narrative_text",
    "section_text": "narrative_text",
    "table": "tables",
    "table_segment": "tables",
    "figure": "figures",
    "numbered_list": "lists",
    "list_segment": "lists",
}


class DataTypeDetector:
    """Map Stage 3 chunk types and metadata to normalized section data types."""

    def detect_for_chunks(self, chunks: Iterable[LDU]) -> list[str]:
        detected: set[str] = set()
        for chunk in chunks:
            data_type = CHUNK_TYPE_TO_DATA_TYPE.get(chunk.chunk_type)
            if data_type:
                detected.add(data_type)
            if chunk.metadata.get("contains_equation"):
                detected.add("equations")
        return sorted(detected)
