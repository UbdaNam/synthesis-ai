"""Deterministic Stage 4 PageIndex tree construction and persistence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.models.ldu import LDU
from src.models.page_index import PageIndexDocument, PageIndexNode


SECTION_NUMBER_RE = re.compile(r"^\s*((?:\d+\.)*\d+)\b")


@dataclass(slots=True)
class BuilderRules:
    artifact_dir: str = ".refinery/pageindex"
    rule_version: str = "pageindex-v1"


def stable_pageindex_id(doc_id: str, section_path: str) -> str:
    digest = sha256(f"{doc_id}:{section_path}".encode("utf-8")).hexdigest()[:12]
    return f"{doc_id}-section-{digest}"


class PageIndexBuilder:
    """Build hierarchical section trees from Stage 3 LDUs."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        config = (rules or {}).get("pageindex", {})
        self.rules = BuilderRules(
            artifact_dir=str(config.get("artifact_dir", ".refinery/pageindex")),
            rule_version=str(config.get("rule_version", "pageindex-v1")),
        )

    def build_document(self, doc_id: str, chunks: list[LDU]) -> PageIndexDocument:
        if not chunks:
            raise ValueError("missing_chunked_document")

        headers = [chunk for chunk in chunks if chunk.chunk_type == "section_header"]
        if headers:
            root_sections = self._build_from_headers(doc_id, chunks, headers)
        else:
            root_sections = [self._build_document_root(doc_id, chunks)]

        return PageIndexDocument(
            doc_id=doc_id,
            root_sections=root_sections,
            section_count=sum(1 for _ in self._flatten(root_sections)),
            chunk_count=len(chunks),
            artifact_path=str(self.artifact_path(doc_id)),
            rule_version=self.rules.rule_version,
            metadata={"chunk_ids": [chunk.id for chunk in chunks]},
        )

    def artifact_path(self, doc_id: str) -> Path:
        return Path(self.rules.artifact_dir) / f"{doc_id}.json"

    def persist_document(self, document: PageIndexDocument) -> Path:
        path = self.artifact_path(document.doc_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        persisted = document.model_copy(update={"artifact_path": str(path)})
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(persisted.model_dump(mode="json"), stream, indent=2, sort_keys=True)
            stream.write("\n")
        return path

    def _build_document_root(self, doc_id: str, chunks: list[LDU]) -> PageIndexNode:
        page_refs = sorted({page for chunk in chunks for page in chunk.page_refs})
        return PageIndexNode(
            id=stable_pageindex_id(doc_id, "Document"),
            doc_id=doc_id,
            title="Document",
            page_start=min(page_refs),
            page_end=max(page_refs),
            child_sections=[],
            key_entities=[],
            summary="",
            data_types_present=[],
            parent_section_id=None,
            chunk_ids=[chunk.id for chunk in chunks],
            metadata={
                "section_path": "Document",
                "direct_chunk_ids": [chunk.id for chunk in chunks],
                "content_hashes": [chunk.content_hash for chunk in chunks],
            },
        )

    def _build_from_headers(
        self, doc_id: str, chunks: list[LDU], headers: list[LDU]
    ) -> list[PageIndexNode]:
        ordered_headers = sorted(headers, key=lambda chunk: (min(chunk.page_refs), chunk.id))
        title_to_header = {header.content.strip(): header for header in ordered_headers}
        number_to_title: dict[str, str] = {}
        parent_map: dict[str, str | None] = {}

        for header in ordered_headers:
            title = header.content.strip()
            section_number = self._extract_section_number(title)
            parent_title: str | None = None
            if section_number:
                number_to_title[section_number] = title
                parent_number = self._parent_number(section_number)
                parent_title = number_to_title.get(parent_number) if parent_number else None
            parent_map[title] = parent_title

        direct_chunks: dict[str, list[LDU]] = {title: [] for title in title_to_header}
        for chunk in chunks:
            if chunk.chunk_type == "section_header":
                direct_chunks[chunk.content.strip()].append(chunk)
                continue
            if chunk.parent_section and chunk.parent_section in direct_chunks:
                direct_chunks[chunk.parent_section].append(chunk)

        root_titles = [title for title, parent in parent_map.items() if parent is None]
        return [
            self._build_node_tree(
                doc_id=doc_id,
                title=title,
                parent_title=None,
                parent_path=None,
                parent_map=parent_map,
                direct_chunks=direct_chunks,
            )
            for title in root_titles
        ]

    def _build_node_tree(
        self,
        *,
        doc_id: str,
        title: str,
        parent_title: str | None,
        parent_path: str | None,
        parent_map: dict[str, str | None],
        direct_chunks: dict[str, list[LDU]],
    ) -> PageIndexNode:
        child_titles = [candidate for candidate, parent in parent_map.items() if parent == title]
        section_path = title if not parent_path else f"{parent_path} > {title}"
        node_id = stable_pageindex_id(doc_id, section_path)
        children = [
            self._build_node_tree(
                doc_id=doc_id,
                title=child_title,
                parent_title=title,
                parent_path=section_path,
                parent_map=parent_map,
                direct_chunks=direct_chunks,
            )
            for child_title in child_titles
        ]
        chunk_ids = [chunk.id for chunk in direct_chunks.get(title, [])]
        for child in children:
            chunk_ids.extend(child.chunk_ids or [])
        chunk_ids = list(dict.fromkeys(chunk_ids))

        page_refs = sorted({page for chunk in direct_chunks.get(title, []) for page in chunk.page_refs})
        for child in children:
            page_refs.extend(range(child.page_start, child.page_end + 1))
        dedup_page_refs = sorted(set(page_refs))
        if not dedup_page_refs:
            raise ValueError("invalid_section_hierarchy")
        return PageIndexNode(
            id=node_id,
            doc_id=doc_id,
            title=title,
            page_start=min(dedup_page_refs),
            page_end=max(dedup_page_refs),
            child_sections=[
                child.model_copy(update={"parent_section_id": node_id}) for child in children
            ],
            key_entities=[],
            summary="",
            data_types_present=[],
            parent_section_id=stable_pageindex_id(doc_id, parent_path) if parent_path else None,
            chunk_ids=chunk_ids,
            metadata={
                "section_path": section_path,
                "direct_chunk_ids": [chunk.id for chunk in direct_chunks.get(title, [])],
                "content_hashes": [chunk.content_hash for chunk in direct_chunks.get(title, [])],
                "header_number": self._extract_section_number(title),
            },
        )

    @staticmethod
    def _flatten(nodes: list[PageIndexNode]):
        for node in nodes:
            yield node
            yield from PageIndexBuilder._flatten(node.child_sections)

    @staticmethod
    def _extract_section_number(title: str) -> str | None:
        match = SECTION_NUMBER_RE.match(title)
        return match.group(1) if match else None

    @staticmethod
    def _parent_number(section_number: str | None) -> str | None:
        if not section_number or "." not in section_number:
            return None
        return section_number.rsplit(".", 1)[0]
