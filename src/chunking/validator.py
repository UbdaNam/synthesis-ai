"""Explicit Stage 3 chunk validation rules."""

from __future__ import annotations

from src.models.ldu import LDU


class ChunkValidationError(ValueError):
    """Raised when Stage 3 chunk validation fails."""


class ChunkValidator:
    """Enforce Stage 3 chunking invariants."""

    def validate(self, chunks: list[LDU]) -> list[LDU]:
        if not chunks:
            raise ChunkValidationError("no_ldus_emitted")

        known_ids = {chunk.id for chunk in chunks}
        for chunk in chunks:
            if not chunk.content or not chunk.content_hash:
                raise ChunkValidationError("missing_required_fields")
            if not chunk.page_refs:
                raise ChunkValidationError("missing_page_refs")
            if chunk.metadata.get("section_context_active") and not chunk.parent_section:
                raise ChunkValidationError("missing_parent_section")

            if chunk.chunk_type in {"table", "table_segment"}:
                headers = chunk.metadata.get("headers") or []
                if not headers:
                    raise ChunkValidationError("table_header_missing")
                if chunk.metadata.get("row_count", 0) > 0 and " | ".join(headers) not in chunk.content:
                    raise ChunkValidationError("table_header_not_repeated")

            if chunk.chunk_type == "figure" and chunk.metadata.get("source_caption_exists"):
                if not chunk.metadata.get("caption"):
                    raise ChunkValidationError("figure_caption_missing")

            if chunk.chunk_type in {"numbered_list", "list_segment"}:
                list_items = chunk.metadata.get("list_items") or []
                if not list_items:
                    raise ChunkValidationError("numbered_list_items_missing")
                if chunk.chunk_type == "list_segment" and "list_continuation" not in chunk.metadata:
                    raise ChunkValidationError("numbered_list_continuity_missing")

            for relationship in chunk.relationships:
                if relationship.resolved and relationship.target_chunk_id not in known_ids:
                    raise ChunkValidationError("relationship_target_missing")

            refs = {rel.relationship_type for rel in chunk.relationships}
            if "Table " in chunk.content and "references_table" not in refs:
                raise ChunkValidationError("table_reference_not_resolved")
            if "Figure " in chunk.content and "references_figure" not in refs:
                raise ChunkValidationError("figure_reference_not_resolved")
            if "Section " in chunk.content and "references_section" not in refs:
                raise ChunkValidationError("section_reference_not_resolved")

        return chunks
