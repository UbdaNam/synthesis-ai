"""Real semantic search tool over the local Chroma vector database."""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from src.config.env import ensure_env_loaded
from src.indexing.vector_ingestor import _LangChainEmbeddingAdapter
from src.models.ldu import LDU
from src.models.query_result import SemanticSearchHit, SemanticSearchResult
from src.query.chroma_client import create_persistent_client
from src.query import QueryArtifactPaths, QueryStageError, load_ldu_cache, load_rules


class SemanticSearchToolInput(BaseModel):
    """Arguments accepted by the semantic_search tool."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    section_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)


class SemanticSearchService:
    """Search retrieval-ready LDUs through Chroma and restore provenance."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or load_rules()
        query_cfg = self.rules.get("query", {})
        pageindex_cfg = self.rules.get("pageindex", {})
        self.collection_name = str(query_cfg.get("vector_collection_name", pageindex_cfg.get("vector_collection_name", "pageindex-ldus")))
        self.persist_directory = str(
            os.getenv(
                "PAGEINDEX_VECTOR_PERSIST_DIRECTORY",
                query_cfg.get("vector_persist_directory", pageindex_cfg.get("vector_persist_directory", ".refinery/pageindex/chroma")),
            )
        )
        self.embedding_model = str(query_cfg.get("embedding_model", pageindex_cfg.get("embedding_model", "openai/text-embedding-3-small")))
        self.embedding_base_url = str(query_cfg.get("embedding_base_url", pageindex_cfg.get("embedding_base_url", "https://openrouter.ai/api/v1")))
        self.paths = QueryArtifactPaths(self.rules)
        self._runtime_chunks: dict[str, dict[str, LDU]] = {}

    def set_runtime_chunks(self, doc_id: str, chunks: list[LDU]) -> None:
        self._runtime_chunks[doc_id] = {chunk.id: chunk for chunk in chunks}

    def search(self, doc_id: str, query: str, section_ids: list[str] | None = None, limit: int = 5) -> SemanticSearchResult:
        section_ids = section_ids or []
        collection = self._collection()
        payload = collection.query(query_texts=[query], n_results=max(limit * 3, limit))
        chunk_map = self._load_chunks(doc_id)
        ids = payload.get("ids", [[]])[0]
        documents = payload.get("documents", [[]])[0]
        metadatas = payload.get("metadatas", [[]])[0]
        distances = payload.get("distances", [[]])[0] if payload.get("distances") else [0.0] * len(ids)
        hits: list[SemanticSearchHit] = []
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances, strict=True):
            if chunk_id not in chunk_map:
                continue
            chunk = chunk_map[chunk_id]
            section_id = str(metadata.get("section_id", "") or chunk.metadata.get("section_id") or chunk.parent_section or "") or None
            if section_ids and section_id not in section_ids:
                continue
            score = 1.0 / (1.0 + float(distance))
            hits.append(
                SemanticSearchHit(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    section_id=section_id,
                    content=document,
                    score=score,
                    page_refs=chunk.page_refs,
                    bounding_box=chunk.bounding_box,
                    content_hash=chunk.content_hash,
                    chunk_type=chunk.chunk_type,
                )
            )
        ordered = sorted(hits, key=lambda item: (-item.score, item.page_refs[0], item.chunk_id))[:limit]
        return SemanticSearchResult(doc_id=doc_id, query=query, section_filters=section_ids, hits=ordered)

    def build_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=lambda doc_id, query, section_ids=None, limit=5: self.search(doc_id=doc_id, query=query, section_ids=section_ids or [], limit=limit).model_dump(mode="json"),
            name="semantic_search",
            description="Search retrieval-ready document chunks in the local vector database and return grounded hits with provenance metadata.",
            args_schema=SemanticSearchToolInput,
        )

    def _collection(self) -> Any:
        try:
            client = create_persistent_client(self.persist_directory)
        except ImportError as exc:  # pragma: no cover
            raise QueryStageError("semantic_search_failed") from exc
        return client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_function(),
        )

    def _embedding_function(self) -> Any:
        ensure_env_loaded()
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise QueryStageError("semantic_search_failed") from exc
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise QueryStageError("semantic_search_failed")
        embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=api_key,
            base_url=self.embedding_base_url,
        )
        return _LangChainEmbeddingAdapter(embeddings)

    def _load_chunks(self, doc_id: str) -> dict[str, LDU]:
        if doc_id in self._runtime_chunks:
            return self._runtime_chunks[doc_id]
        return {chunk.id: chunk for chunk in load_ldu_cache(doc_id, self.rules)}
