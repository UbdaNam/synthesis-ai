"""Real local vector ingestion for Stage 4 using ChromaDB."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from src.config.env import ensure_env_loaded
from src.models.ldu import LDU
from src.query.chroma_client import create_persistent_client


class VectorIngestionError(RuntimeError):
    """Raised when Stage 4 vector ingestion fails."""


class VectorIngestor:
    """Persist Stage 3 LDUs into a local Chroma collection."""

    def __init__(
        self,
        rules: dict[str, Any] | None = None,
        client_factory: Callable[[str], Any] | None = None,
    ) -> None:
        config = (rules or {}).get("pageindex", {})
        self.collection_name = str(config.get("vector_collection_name", "pageindex-ldus"))
        self.embedding_model = str(
            config.get("embedding_model", "openai/text-embedding-3-small")
        )
        self.embedding_base_url = str(
            config.get("embedding_base_url", "https://openrouter.ai/api/v1")
        )
        self.persist_directory = str(
            os.getenv(
                "PAGEINDEX_VECTOR_PERSIST_DIRECTORY",
                config.get("vector_persist_directory", ".refinery/pageindex/chroma"),
            )
        )
        self.client_factory = client_factory

    def ingest(
        self,
        chunks: list[LDU],
        chunk_section_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        if not chunks:
            return {"ingested_count": 0, "collection_name": self.collection_name}
        client = self.client_factory(self.persist_directory) if self.client_factory else self._default_client()
        collection = client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_function(),
        )
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [self._metadata_for_chunk(chunk, chunk_section_map.get(chunk.id, {})) for chunk in chunks]
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return {
            "ingested_count": len(ids),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }

    def _default_client(self) -> Any:
        try:
            return create_persistent_client(self.persist_directory)
        except ImportError as exc:  # pragma: no cover - runtime dependency guard
            raise VectorIngestionError("vector_ingestion_failed") from exc

    def _embedding_function(self) -> Any:
        ensure_env_loaded()
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:  # pragma: no cover - runtime dependency guard
            raise VectorIngestionError("vector_ingestion_failed") from exc
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise VectorIngestionError("vector_ingestion_failed")
        embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=api_key,
            base_url=self.embedding_base_url,
        )
        return _LangChainEmbeddingAdapter(embeddings)

    @staticmethod
    def _metadata_for_chunk(chunk: LDU, section_meta: dict[str, Any]) -> dict[str, Any]:
        return {
            "doc_id": chunk.doc_id,
            "section_id": str(section_meta.get("section_id", "")),
            "section_title": str(section_meta.get("section_title", "")),
            "page_number": min(chunk.page_refs),
            "page_refs": ",".join(str(page) for page in chunk.page_refs),
            "bounding_box": ",".join(
                str(value)
                for value in (
                    chunk.bounding_box.x0,
                    chunk.bounding_box.y0,
                    chunk.bounding_box.x1,
                    chunk.bounding_box.y1,
                )
            ),
            "chunk_type": chunk.chunk_type,
            "content_hash": chunk.content_hash,
        }


class _LangChainEmbeddingAdapter:
    """Adapt a LangChain embeddings client to Chroma's embedding-function shape."""

    def __init__(self, embeddings: Any) -> None:
        self._embeddings = embeddings

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(input)

    def embed_query(self, input: str | list[str]) -> list[list[float]] | list[float]:
        if isinstance(input, list):
            return [self._embeddings.embed_query(text) for text in input]
        return self._embeddings.embed_query(input)

    @staticmethod
    def name() -> str:
        return "langchain_openai_embeddings"

    @staticmethod
    def is_legacy() -> bool:
        return False

    @staticmethod
    def default_space() -> str:
        return "cosine"

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def get_config() -> dict[str, Any]:
        return {"name": "langchain_openai_embeddings", "space": "cosine"}
