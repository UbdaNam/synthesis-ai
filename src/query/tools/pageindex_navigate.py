"""Real tool for deterministic PageIndex navigation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from src.models.page_index import PageIndexDocument, PageIndexNode
from src.models.query_result import NavigationSectionHit, PageIndexNavigationResult
from src.query import QueryArtifactPaths, QueryStageError, load_rules


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class NavigationToolInput(BaseModel):
    """Arguments accepted by the PageIndex navigation tool."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class PageIndexNavigateService:
    """Read and rank persisted PageIndex sections for a topic."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or load_rules()
        self.paths = QueryArtifactPaths(self.rules)
        self._runtime_page_indexes: dict[str, PageIndexDocument] = {}

    def set_runtime_page_index(self, document: PageIndexDocument) -> None:
        self._runtime_page_indexes[document.doc_id] = document

    def navigate(self, doc_id: str, topic: str, limit: int = 5) -> PageIndexNavigationResult:
        document = self._load_page_index(doc_id)
        topic_terms = {token.lower() for token in TOKEN_RE.findall(topic)}
        hits: list[NavigationSectionHit] = []
        for node in document.flatten_nodes():
            title_terms = {token.lower() for token in TOKEN_RE.findall(node.title)}
            entity_terms = {
                token.lower()
                for entity in node.key_entities
                for token in TOKEN_RE.findall(entity)
            }
            summary_terms = {token.lower() for token in TOKEN_RE.findall(node.summary)}
            data_terms = {token.lower() for token in node.data_types_present}
            matched = sorted(topic_terms & (title_terms | entity_terms | summary_terms | data_terms))
            score = float(
                4 * len(topic_terms & title_terms)
                + 2 * len(topic_terms & entity_terms)
                + 1 * len(topic_terms & summary_terms)
                + 1 * len(topic_terms & data_terms)
            )
            if score <= 0 and topic_terms:
                continue
            hits.append(
                NavigationSectionHit(
                    section_id=node.id,
                    title=node.title,
                    page_start=node.page_start,
                    page_end=node.page_end,
                    score=score,
                    summary=node.summary,
                    child_section_ids=[child.id for child in node.child_sections],
                    matched_terms=matched,
                )
            )
        ordered = sorted(hits, key=lambda item: (-item.score, item.page_start, item.title))[:limit]
        return PageIndexNavigationResult(doc_id=doc_id, query=topic, matched_sections=ordered)

    def build_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=lambda doc_id, topic, limit=5: self.navigate(doc_id=doc_id, topic=topic, limit=limit).model_dump(mode="json"),
            name="pageindex_navigate",
            description="Navigate a persisted PageIndex to find the most relevant sections for a topic before deeper retrieval.",
            args_schema=NavigationToolInput,
        )

    def _load_page_index(self, doc_id: str) -> PageIndexDocument:
        if doc_id in self._runtime_page_indexes:
            return self._runtime_page_indexes[doc_id]
        artifact_dir = Path(str(self.rules.get("pageindex", {}).get("artifact_dir", ".refinery/pageindex")))
        path = artifact_dir / f"{doc_id}.json"
        if not path.exists():
            raise QueryStageError("missing_page_index")
        return PageIndexDocument.model_validate(json.loads(path.read_text(encoding="utf-8")))
