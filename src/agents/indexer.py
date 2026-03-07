"""Stage 4 PageIndex Builder entrypoint."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any

import yaml

from src.indexing.data_type_detector import DataTypeDetector
from src.indexing.entity_extractor import EntityExtractor
from src.indexing.pageindex_builder import PageIndexBuilder
from src.indexing.section_summarizer import SectionSummarizer, SummaryGenerationError
from src.indexing.vector_ingestor import VectorIngestionError, VectorIngestor
from src.models.graph_state import GraphState
from src.models.ldu import LDU
from src.models.page_index import PageIndexDocument, PageIndexNode, SectionCandidate


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _load_rules(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as stream:
        loaded = yaml.safe_load(stream) or {}
    if "pageindex" not in loaded:
        loaded["pageindex"] = {}
    return loaded


class PageIndexingAgent:
    """Public Stage 4 entrypoint for page indexing and retrieval preparation."""

    def __init__(
        self,
        config_path: str = "rubric/extraction_rules.yaml",
        builder: PageIndexBuilder | None = None,
        entity_extractor: EntityExtractor | None = None,
        data_type_detector: DataTypeDetector | None = None,
        summarizer: SectionSummarizer | None = None,
        vector_ingestor: VectorIngestor | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self.config_path = config_path
        self.rules = _load_rules(config_path)
        config = self.rules.get("pageindex", {})
        self.builder = builder or PageIndexBuilder(self.rules)
        self.entity_extractor = entity_extractor or EntityExtractor(
            stopwords=config.get("entity_extraction_stopwords", []),
            max_entities=int(config.get("entity_max_per_section", 8)),
        )
        self.data_type_detector = data_type_detector or DataTypeDetector()
        self.summarizer = summarizer or SectionSummarizer(self.rules)
        self.vector_ingestor = vector_ingestor or VectorIngestor(self.rules)
        self.enable_vector_ingestion = bool(config.get("enable_vector_ingestion", True))
        self.timer = timer or time.perf_counter

    def index_node(self, state: GraphState) -> GraphState:
        if not state.chunked_document:
            return state.model_copy(
                update={
                    "page_index": None,
                    "page_index_path": None,
                    "section_candidates": [],
                    "indexing_error": "missing_chunked_document",
                    "indexing_meta": {"rule_version": self._rule_version()},
                }
            )
        if any(chunk.doc_id != state.doc_id for chunk in state.chunked_document):
            return state.model_copy(
                update={
                    "page_index": None,
                    "page_index_path": None,
                    "section_candidates": [],
                    "indexing_error": "mixed_document_ids",
                    "indexing_meta": {"rule_version": self._rule_version()},
                }
            )

        started = self.timer()
        try:
            document = self.builder.build_document(state.doc_id, state.chunked_document)
            document = self._enrich_document(document, state.chunked_document)
            artifact_path = self.builder.persist_document(document)
            vector_meta = {"enabled": False, "ingested_count": 0}
            if self.enable_vector_ingestion:
                vector_meta = self.vector_ingestor.ingest(
                    state.chunked_document,
                    self._chunk_section_map(document),
                )
                vector_meta["enabled"] = True
        except (ValueError, SummaryGenerationError, VectorIngestionError) as exc:
            elapsed = max(0.0, self.timer() - started)
            return state.model_copy(
                update={
                    "page_index": None,
                    "page_index_path": None,
                    "section_candidates": [],
                    "indexing_error": str(exc),
                    "indexing_meta": {
                        "rule_version": self._rule_version(),
                        "processing_time": elapsed,
                        "status": "failed_closed",
                    },
                }
            )

        elapsed = max(0.0, self.timer() - started)
        meta = {
            "rule_version": self._rule_version(),
            "processing_time": elapsed,
            "status": "validated",
            "section_count": document.section_count,
            "chunk_count": document.chunk_count,
            "vector_ingestion": vector_meta,
            "artifact_path": str(artifact_path),
        }
        return state.model_copy(
            update={
                "page_index": document.model_copy(update={"artifact_path": str(artifact_path)}),
                "page_index_path": str(artifact_path),
                "section_candidates": [],
                "indexing_error": None,
                "indexing_meta": meta,
            }
        )

    def rank_sections_for_topic(
        self, topic: str, document: PageIndexDocument, limit: int = 5
    ) -> list[SectionCandidate]:
        topic_terms = {token.lower() for token in TOKEN_RE.findall(topic)}
        candidates: list[SectionCandidate] = []
        for node in document.flatten_nodes():
            title_terms = {token.lower() for token in TOKEN_RE.findall(node.title)}
            entity_terms = {
                token.lower()
                for entity in node.key_entities
                for token in TOKEN_RE.findall(entity)
            }
            summary_terms = {token.lower() for token in TOKEN_RE.findall(node.summary)}
            matched = sorted(topic_terms & (title_terms | entity_terms | summary_terms))
            score = (
                3 * len(topic_terms & title_terms)
                + 2 * len(topic_terms & entity_terms)
                + 1 * len(topic_terms & summary_terms)
            )
            candidates.append(
                SectionCandidate(
                    section_id=node.id,
                    title=node.title,
                    score=float(score),
                    page_start=node.page_start,
                    page_end=node.page_end,
                    matched_terms=matched,
                )
            )
        return sorted(candidates, key=lambda item: (-item.score, item.page_start, item.title))[
            :limit
        ]

    def _enrich_document(self, document: PageIndexDocument, chunks: list[LDU]) -> PageIndexDocument:
        chunk_map = {chunk.id: chunk for chunk in chunks}
        enriched_roots = [self._enrich_node(node, chunk_map) for node in document.root_sections]
        return PageIndexDocument(
            doc_id=document.doc_id,
            root_sections=enriched_roots,
            section_count=document.section_count,
            chunk_count=document.chunk_count,
            artifact_path=document.artifact_path,
            rule_version=document.rule_version,
            generated_at=document.generated_at,
            metadata=document.metadata,
        )

    def _enrich_node(self, node: PageIndexNode, chunk_map: dict[str, LDU]) -> PageIndexNode:
        children = [self._enrich_node(child, chunk_map) for child in node.child_sections]
        node_chunks = [
            chunk_map[chunk_id]
            for chunk_id in (node.chunk_ids or [])
            if chunk_id in chunk_map
        ]
        entities = self.entity_extractor.extract_for_chunks(node_chunks)
        data_types = self.data_type_detector.detect_for_chunks(node_chunks)
        summary_request = self.summarizer.build_request(
            doc_id=node.doc_id,
            section_id=node.id,
            section_title=node.title,
            chunks=node_chunks,
        )
        summary = self.summarizer.summarize_section(summary_request)
        return node.model_copy(
            update={
                "child_sections": children,
                "key_entities": entities,
                "data_types_present": data_types,
                "summary": summary.summary,
                "metadata": {
                    **node.metadata,
                    "summary_source_chunk_ids": summary.source_chunk_ids,
                },
            }
        )

    @staticmethod
    def _chunk_section_map(document: PageIndexDocument) -> dict[str, dict[str, Any]]:
        mapping: dict[str, dict[str, Any]] = {}
        for node in document.flatten_nodes():
            for chunk_id in node.metadata.get("direct_chunk_ids", []):
                mapping[chunk_id] = {"section_id": node.id, "section_title": node.title}
        return mapping

    def _rule_version(self) -> str:
        return str(self.rules.get("pageindex", {}).get("rule_version", "pageindex-v1"))
