"""Bounded OpenRouter-backed section summary generation for Stage 4."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.config.env import ensure_env_loaded
from src.models.ldu import LDU
from src.models.page_index import SectionSummaryRequest, SectionSummaryResult


class SummaryGenerationError(RuntimeError):
    """Raised when Stage 4 summary generation fails closed."""


class SectionSummarizer:
    """Generate structured section summaries using OpenRouter."""

    def __init__(
        self,
        rules: dict[str, Any] | None = None,
        llm_factory: Callable[[], Any] | None = None,
    ) -> None:
        config = (rules or {}).get("pageindex", {})
        self.model_name = str(config.get("summary_model_name", "openai/gpt-4o-mini"))
        self.max_chunks = int(config.get("max_chunks_per_summary_request", 6))
        self.temperature = float(config.get("summary_temperature", 0.0))
        self.llm_factory = llm_factory

    def build_request(
        self, doc_id: str, section_id: str, section_title: str, chunks: list[LDU]
    ) -> SectionSummaryRequest:
        bounded_chunks = chunks[: self.max_chunks]
        return SectionSummaryRequest(
            doc_id=doc_id,
            section_id=section_id,
            section_title=section_title,
            chunk_ids=[chunk.id for chunk in bounded_chunks],
            source_chunks=[chunk.content for chunk in bounded_chunks],
        )

    def summarize_section(self, request: SectionSummaryRequest) -> SectionSummaryResult:
        llm = self.llm_factory() if self.llm_factory else self._default_llm()
        messages = [
            (
                "system",
                "You summarize document sections. Use only the supplied source chunks. "
                "Return exactly 2-3 factual sentences and never invent details.",
            ),
            ("human", self._render_prompt(request)),
        ]
        try:
            structured = llm.with_structured_output(SectionSummaryResult)
            result = structured.invoke(messages)
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise SummaryGenerationError("summary_generation_failed") from exc
        if isinstance(result, dict):
            result = SectionSummaryResult.model_validate(result)
        if result.section_id != request.section_id:
            result = result.model_copy(update={"section_id": request.section_id})
        if not result.source_chunk_ids:
            result = result.model_copy(update={"source_chunk_ids": request.chunk_ids})
        elif not set(result.source_chunk_ids).issubset(set(request.chunk_ids)):
            filtered = [chunk_id for chunk_id in request.chunk_ids if chunk_id in result.source_chunk_ids]
            result = result.model_copy(update={"source_chunk_ids": filtered or request.chunk_ids})
        return result

    def _default_llm(self) -> Any:
        ensure_env_loaded()
        try:
            from langchain_openrouter import ChatOpenRouter
        except ImportError as exc:  # pragma: no cover - runtime dependency guard
            raise SummaryGenerationError("summary_generation_failed") from exc
        return ChatOpenRouter(model=self.model_name, temperature=self.temperature)

    @staticmethod
    def _render_prompt(request: SectionSummaryRequest) -> str:
        chunks = "\n\n".join(
            f"Chunk {chunk_id}:\n{content}"
            for chunk_id, content in zip(request.chunk_ids, request.source_chunks, strict=True)
        )
        return (
            f"Document: {request.doc_id}\n"
            f"Section ID: {request.section_id}\n"
            f"Section Title: {request.section_title}\n\n"
            "Source Chunks:\n"
            f"{chunks}\n\n"
            "Return a concise, grounded summary."
        )
