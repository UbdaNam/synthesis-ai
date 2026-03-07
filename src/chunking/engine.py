"""Stage 3 semantic chunk construction engine."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal

from src.chunking.hash_generator import generate_ldu_hash
from src.chunking.reference_resolver import resolve_references
from src.chunking.token_counter import count_tokens
from src.models.chunk_relationship import ChunkRelationship
from src.models.extracted_document import (
    BoundingBox,
    ExtractedDocument,
    FigureBlock,
    StructuredTable,
    TextBlock,
)
from src.models.ldu import ChunkType, LDU


NUMBERED_LIST_PATTERN = re.compile(r"^\s*(?:\d+|[a-zA-Z])[\.\)]\s+")
SECTION_NUMBER_PATTERN = re.compile(r"^\s*((?:\d+\.)*\d+)\b")


@dataclass(slots=True)
class EngineRules:
    max_tokens_per_chunk: int = 200
    numbered_list_split_threshold: int = 200
    table_row_group_limit: int = 20
    reference_resolution_behavior: str = "resolve_if_known"
    section_heading_block_types: tuple[str, ...] = ("heading",)


@dataclass(slots=True)
class _StructuralItem:
    kind: Literal["text", "table", "figure"]
    page_number: int
    y0: float
    x0: float
    reading_order: int
    payload: TextBlock | StructuredTable | FigureBlock


class ChunkingEngine:
    """Transform Stage 2 extracted documents into Stage 3 LDUs."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        config = (rules or {}).get("chunking", {})
        self.rules = EngineRules(
            max_tokens_per_chunk=int(config.get("max_tokens_per_chunk", 200)),
            numbered_list_split_threshold=int(config.get("numbered_list_split_threshold", 200)),
            table_row_group_limit=int(config.get("table_row_group_limit", 20)),
            reference_resolution_behavior=str(
                config.get("reference_resolution_behavior", "resolve_if_known")
            ),
            section_heading_block_types=tuple(
                config.get("section_heading_block_types", ["heading"])
            ),
        )
        self._chunk_index = 0

    def chunk_document(self, document: ExtractedDocument) -> list[LDU]:
        items = self._build_items(document)
        chunks: list[LDU] = []
        active_section_name: str | None = None
        active_section_id: str | None = None
        previous_chunk_id: str | None = None
        table_index = 0
        figure_index = 0
        idx = 0

        while idx < len(items):
            item = items[idx]
            if item.kind == "text":
                block = item.payload
                assert isinstance(block, TextBlock)
                if block.block_type in self.rules.section_heading_block_types:
                    section_chunk = self._make_section_header(document.doc_id, block)
                    chunks.append(section_chunk)
                    previous_chunk_id = section_chunk.id
                    active_section_name = block.text.strip()
                    active_section_id = section_chunk.id
                    idx += 1
                    continue
                if block.block_type == "list_item" and self._is_numbered_list_item(block.text):
                    list_blocks, idx = self._collect_list_blocks(items, idx)
                    list_chunks = self._build_list_chunks(
                        document.doc_id,
                        list_blocks,
                        active_section_name,
                        active_section_id,
                        previous_chunk_id,
                    )
                    if list_chunks:
                        previous_chunk_id = list_chunks[-1].id
                        chunks.extend(list_chunks)
                    continue
                text_blocks, idx = self._collect_text_blocks(items, idx)
                text_chunks = self._build_text_chunks(
                    document.doc_id,
                    text_blocks,
                    active_section_name,
                    active_section_id,
                    previous_chunk_id,
                )
                if text_chunks:
                    previous_chunk_id = text_chunks[-1].id
                    chunks.extend(text_chunks)
                continue

            if item.kind == "table":
                table_index += 1
                table = item.payload
                assert isinstance(table, StructuredTable)
                table_chunks = self._build_table_chunks(
                    document.doc_id,
                    table,
                    table_index,
                    active_section_name,
                    active_section_id,
                    previous_chunk_id,
                )
                previous_chunk_id = table_chunks[-1].id
                chunks.extend(table_chunks)
                idx += 1
                continue

            figure_index += 1
            figure = item.payload
            assert isinstance(figure, FigureBlock)
            figure_chunk = self._build_figure_chunk(
                document.doc_id,
                figure,
                figure_index,
                active_section_name,
                active_section_id,
                previous_chunk_id,
            )
            previous_chunk_id = figure_chunk.id
            chunks.append(figure_chunk)
            idx += 1

        self._attach_cross_references(document.doc_id, chunks)
        return chunks

    def _build_items(self, document: ExtractedDocument) -> list[_StructuralItem]:
        items: list[_StructuralItem] = []
        for block in document.text_blocks:
            items.append(
                _StructuralItem(
                    kind="text",
                    page_number=block.page_number,
                    y0=block.bounding_box.y0,
                    x0=block.bounding_box.x0,
                    reading_order=block.reading_order,
                    payload=block,
                )
            )
        for table in document.tables:
            items.append(
                _StructuralItem(
                    kind="table",
                    page_number=table.page_number,
                    y0=table.bounding_box.y0,
                    x0=table.bounding_box.x0,
                    reading_order=10_000,
                    payload=table,
                )
            )
        for figure in document.figures:
            items.append(
                _StructuralItem(
                    kind="figure",
                    page_number=figure.page_number,
                    y0=figure.bounding_box.y0,
                    x0=figure.bounding_box.x0,
                    reading_order=10_000,
                    payload=figure,
                )
            )
        items.sort(key=lambda item: (item.page_number, item.y0, item.x0, item.reading_order))
        return items

    def _next_id(self, doc_id: str, chunk_type: ChunkType) -> str:
        self._chunk_index += 1
        return f"{doc_id}-{chunk_type}-{self._chunk_index:04d}"

    def _make_section_header(self, doc_id: str, block: TextBlock) -> LDU:
        section_number = self._extract_section_number(block.text)
        metadata = {
            "source_block_ids": [block.id],
            "source_content_hashes": [block.content_hash],
            "section_label": f"Section {section_number}" if section_number else None,
            "section_context_active": False,
        }
        return self._make_chunk(
            doc_id=doc_id,
            content=block.text,
            chunk_type="section_header",
            page_refs=[block.page_number],
            bounding_box=block.bounding_box,
            parent_section=None,
            relationships=[],
            metadata=metadata,
        )

    def _collect_text_blocks(
        self, items: list[_StructuralItem], start: int
    ) -> tuple[list[TextBlock], int]:
        blocks: list[TextBlock] = []
        idx = start
        while idx < len(items):
            item = items[idx]
            if item.kind != "text":
                break
            block = item.payload
            assert isinstance(block, TextBlock)
            if block.block_type in self.rules.section_heading_block_types:
                break
            if block.block_type == "list_item" and self._is_numbered_list_item(block.text):
                break
            blocks.append(block)
            idx += 1
        return blocks, idx

    def _collect_list_blocks(
        self, items: list[_StructuralItem], start: int
    ) -> tuple[list[TextBlock], int]:
        blocks: list[TextBlock] = []
        idx = start
        while idx < len(items):
            item = items[idx]
            if item.kind != "text":
                break
            block = item.payload
            assert isinstance(block, TextBlock)
            if block.block_type != "list_item" or not self._is_numbered_list_item(block.text):
                break
            blocks.append(block)
            idx += 1
        return blocks, idx

    def _build_text_chunks(
        self,
        doc_id: str,
        blocks: list[TextBlock],
        active_section_name: str | None,
        active_section_id: str | None,
        previous_chunk_id: str | None,
    ) -> list[LDU]:
        chunks: list[LDU] = []
        current: list[TextBlock] = []
        current_tokens = 0

        for block in blocks:
            next_tokens = count_tokens(block.text)
            if current and current_tokens + next_tokens > self.rules.max_tokens_per_chunk:
                chunk = self._make_text_chunk(
                    doc_id, current, active_section_name, active_section_id, previous_chunk_id
                )
                previous_chunk_id = chunk.id
                chunks.append(chunk)
                current = []
                current_tokens = 0
            current.append(block)
            current_tokens += next_tokens

        if current:
            chunks.append(
                self._make_text_chunk(
                    doc_id, current, active_section_name, active_section_id, previous_chunk_id
                )
            )
        return chunks

    def _make_text_chunk(
        self,
        doc_id: str,
        blocks: list[TextBlock],
        active_section_name: str | None,
        active_section_id: str | None,
        previous_chunk_id: str | None,
    ) -> LDU:
        content = "\n".join(block.text for block in blocks)
        metadata = {
            "source_block_ids": [block.id for block in blocks],
            "source_content_hashes": [block.content_hash for block in blocks],
            "source_block_types": [block.block_type for block in blocks],
            "section_context_active": active_section_name is not None,
        }
        relationships = self._base_relationships(
            doc_id, previous_chunk_id, active_section_id, active_section_name
        )
        return self._make_chunk(
            doc_id=doc_id,
            content=content,
            chunk_type="section_text",
            page_refs=self._page_refs_from_text(blocks),
            bounding_box=self._aggregate_bbox([block.bounding_box for block in blocks]),
            parent_section=active_section_name,
            relationships=relationships,
            metadata=metadata,
        )

    def _build_list_chunks(
        self,
        doc_id: str,
        blocks: list[TextBlock],
        active_section_name: str | None,
        active_section_id: str | None,
        previous_chunk_id: str | None,
    ) -> list[LDU]:
        groups: list[list[TextBlock]] = []
        current: list[TextBlock] = []
        current_tokens = 0
        threshold = self.rules.numbered_list_split_threshold

        for block in blocks:
            item_tokens = count_tokens(block.text)
            if current and current_tokens + item_tokens > threshold:
                groups.append(current)
                current = []
                current_tokens = 0
            current.append(block)
            current_tokens += item_tokens
        if current:
            groups.append(current)

        split_required = len(groups) > 1
        chunks: list[LDU] = []
        for index, group in enumerate(groups, start=1):
            relationships = self._base_relationships(
                doc_id, previous_chunk_id, active_section_id, active_section_name
            )
            content = "\n".join(block.text for block in group)
            metadata = {
                "source_block_ids": [block.id for block in group],
                "source_content_hashes": [block.content_hash for block in group],
                "list_items": [block.text for block in group],
                "list_continuation": split_required,
                "list_part_index": index,
                "list_part_count": len(groups),
                "section_context_active": active_section_name is not None,
            }
            chunk = self._make_chunk(
                doc_id=doc_id,
                content=content,
                chunk_type="list_segment" if split_required else "numbered_list",
                page_refs=self._page_refs_from_text(group),
                bounding_box=self._aggregate_bbox([block.bounding_box for block in group]),
                parent_section=active_section_name,
                relationships=relationships,
                metadata=metadata,
            )
            previous_chunk_id = chunk.id
            chunks.append(chunk)
        return chunks

    def _build_table_chunks(
        self,
        doc_id: str,
        table: StructuredTable,
        table_index: int,
        active_section_name: str | None,
        active_section_id: str | None,
        previous_chunk_id: str | None,
    ) -> list[LDU]:
        rows = table.rows or []
        row_groups = [
            rows[i : i + self.rules.table_row_group_limit]
            for i in range(0, len(rows), self.rules.table_row_group_limit)
        ] or [[]]
        table_label = f"Table {table_index}"
        chunks: list[LDU] = []
        split_required = len(row_groups) > 1
        for index, group in enumerate(row_groups, start=1):
            content_lines = [" | ".join(table.headers)]
            content_lines.extend(" | ".join(row) for row in group)
            metadata = {
                "headers": table.headers,
                "row_count": len(group),
                "caption": table.caption,
                "table_label": table_label,
                "source_table_id": table.id,
                "source_content_hashes": [table.content_hash],
                "section_context_active": active_section_name is not None,
                "split_table": split_required,
                "table_part_index": index,
                "table_part_count": len(row_groups),
            }
            relationships = self._base_relationships(
                doc_id, previous_chunk_id, active_section_id, active_section_name
            )
            chunk = self._make_chunk(
                doc_id=doc_id,
                content="\n".join(content_lines).strip(),
                chunk_type="table_segment" if split_required else "table",
                page_refs=[table.page_number],
                bounding_box=table.bounding_box,
                parent_section=active_section_name,
                relationships=relationships,
                metadata=metadata,
            )
            previous_chunk_id = chunk.id
            chunks.append(chunk)
        return chunks

    def _build_figure_chunk(
        self,
        doc_id: str,
        figure: FigureBlock,
        figure_index: int,
        active_section_name: str | None,
        active_section_id: str | None,
        previous_chunk_id: str | None,
    ) -> LDU:
        content = (figure.caption or "").strip() or f"[Figure: {figure.figure_type}]"
        metadata = {
            "caption": figure.caption,
            "figure_type": figure.figure_type,
            "figure_label": f"Figure {figure_index}",
            "source_figure_id": figure.id,
            "source_caption_exists": bool(figure.caption),
            "source_content_hashes": [figure.content_hash],
            "section_context_active": active_section_name is not None,
        }
        relationships = self._base_relationships(
            doc_id, previous_chunk_id, active_section_id, active_section_name
        )
        return self._make_chunk(
            doc_id=doc_id,
            content=content,
            chunk_type="figure",
            page_refs=[figure.page_number],
            bounding_box=figure.bounding_box,
            parent_section=active_section_name,
            relationships=relationships,
            metadata=metadata,
        )

    def _make_chunk(
        self,
        *,
        doc_id: str,
        content: str,
        chunk_type: ChunkType,
        page_refs: list[int],
        bounding_box: BoundingBox,
        parent_section: str | None,
        relationships: list[ChunkRelationship],
        metadata: dict[str, Any],
    ) -> LDU:
        token_count = count_tokens(content)
        content_hash = generate_ldu_hash(
            content=content,
            chunk_type=chunk_type,
            page_refs=page_refs,
            parent_section=parent_section,
            metadata=metadata,
        )
        chunk = LDU(
            id=self._next_id(doc_id, chunk_type),
            doc_id=doc_id,
            content=content,
            chunk_type=chunk_type,
            page_refs=sorted(set(page_refs)),
            bounding_box=bounding_box,
            parent_section=parent_section,
            token_count=token_count,
            content_hash=content_hash,
            relationships=[],
            metadata=metadata,
        )
        chunk.relationships = [
            relationship.model_copy(update={"source_chunk_id": chunk.id})
            for relationship in relationships
        ]
        return chunk

    def _base_relationships(
        self,
        doc_id: str,
        previous_chunk_id: str | None,
        active_section_id: str | None,
        active_section_name: str | None,
    ) -> list[ChunkRelationship]:
        relationships: list[ChunkRelationship] = []
        if active_section_id and active_section_name:
            relationships.append(
                ChunkRelationship(
                    id=f"rel-{stable_id(doc_id, active_section_id, 'belongs_to_section')}",
                    doc_id=doc_id,
                    source_chunk_id="pending",
                    target_chunk_id=active_section_id,
                    relationship_type="belongs_to_section",
                    target_label=active_section_name,
                    resolved=True,
                )
            )
        if previous_chunk_id:
            relationships.append(
                ChunkRelationship(
                    id=f"rel-{stable_id(doc_id, previous_chunk_id, 'follows')}",
                    doc_id=doc_id,
                    source_chunk_id="pending",
                    target_chunk_id=previous_chunk_id,
                    relationship_type="follows",
                    target_label=previous_chunk_id,
                    resolved=True,
                )
            )
        return relationships

    def _attach_cross_references(self, doc_id: str, chunks: list[LDU]) -> None:
        known_targets: dict[str, str] = {}
        for chunk in chunks:
            if chunk.chunk_type in {"table", "table_segment"}:
                label = chunk.metadata.get("table_label")
                if isinstance(label, str) and label not in known_targets:
                    known_targets[label] = chunk.id
            if chunk.chunk_type == "figure":
                label = chunk.metadata.get("figure_label")
                if isinstance(label, str) and label not in known_targets:
                    known_targets[label] = chunk.id
            if chunk.chunk_type == "section_header":
                label = chunk.metadata.get("section_label")
                if isinstance(label, str) and label not in known_targets:
                    known_targets[label] = chunk.id

        for chunk in chunks:
            chunk.relationships.extend(
                resolve_references(
                    doc_id=doc_id,
                    source_chunk_id=chunk.id,
                    content=chunk.content,
                    known_targets=known_targets,
                )
            )

    @staticmethod
    def _extract_section_number(text: str) -> str | None:
        match = SECTION_NUMBER_PATTERN.match(text)
        return match.group(1) if match else None

    @staticmethod
    def _is_numbered_list_item(text: str) -> bool:
        return NUMBERED_LIST_PATTERN.match(text) is not None

    @staticmethod
    def _page_refs_from_text(blocks: list[TextBlock]) -> list[int]:
        return sorted({block.page_number for block in blocks})

    @staticmethod
    def _aggregate_bbox(boxes: list[BoundingBox]) -> BoundingBox:
        return BoundingBox(
            x0=min(box.x0 for box in boxes),
            y0=min(box.y0 for box in boxes),
            x1=max(box.x1 for box in boxes),
            y1=max(box.y1 for box in boxes),
        )


def stable_id(doc_id: str, value: str, suffix: str) -> str:
    """Create a stable short identifier suffix for relationships."""

    return generate_ldu_hash(
        content=value,
        chunk_type=suffix,
        page_refs=[],
        parent_section=None,
        metadata={"doc_id": doc_id},
    )[:12]
