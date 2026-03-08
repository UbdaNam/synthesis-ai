"""Stage 5 Query Agent and provenance-aware LangGraph execution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config.env import ensure_env_loaded
from src.models.graph_state import GraphState
from src.models.provenance_chain import ProvenanceChainItem
from src.models.query_result import (
    AuditDecisionDraft,
    AuditResult,
    PageIndexNavigationResult,
    QueryAnswerDraft,
    QueryRequest,
    QueryResult,
    RetrievalToolName,
    SemanticSearchHit,
    SemanticSearchResult,
    StructuredQueryResult,
    StructuredQueryRow,
)
from src.query import QueryStageError, load_rules
from src.query.audit_mode import AuditModeEvaluator
from src.query.fact_table_extractor import FactTableExtractor
from src.query.tools.pageindex_navigate import PageIndexNavigateService
from src.query.tools.semantic_search import SemanticSearchService
from src.query.tools.structured_query import StructuredQueryService


FACT_HEAVY_RE = re.compile(
    r"\b(revenue|amount|total|balance|ratio|margin|date|period|invoice|expense|expenditure|profit|tax|fiscal)\b",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"\b(section|chapter|overview|summary|appendix|where|which part|which section)\b", re.IGNORECASE)


class QueryAgentError(RuntimeError):
    """Raised when the Query Agent fails closed."""


class _QueryRuntimeState(TypedDict):
    query_request: QueryRequest
    doc_name: str
    messages: list[Any]
    retrieval_path_used: list[str]
    navigation_candidates: list[PageIndexNavigationResult]
    semantic_hits: list[SemanticSearchHit]
    structured_rows: list[StructuredQueryRow]
    final_result: QueryResult | None
    query_error: str | None
    step_count: int


@dataclass(slots=True)
class _RuntimeArtifacts:
    """In-memory artifacts exposed to the Stage 5 tools during one run."""

    doc_id: str
    doc_name: str


class QueryAgent:
    """Production-oriented LangGraph query agent with exactly three tools."""

    def __init__(
        self,
        config_path: str = "rubric/extraction_rules.yaml",
        pageindex_service: PageIndexNavigateService | None = None,
        semantic_service: SemanticSearchService | None = None,
        structured_service: StructuredQueryService | None = None,
        fact_extractor: FactTableExtractor | None = None,
        llm_factory: Any | None = None,
    ) -> None:
        self.config_path = config_path
        self.rules = load_rules(config_path)
        self.config = self.rules.get("query", {})
        self.pageindex_service = pageindex_service or PageIndexNavigateService(self.rules)
        self.semantic_service = semantic_service or SemanticSearchService(self.rules)
        self.structured_service = structured_service or StructuredQueryService(self.rules)
        self.fact_extractor = fact_extractor or FactTableExtractor(self.rules)
        self.max_iterations = int(self.config.get("max_iterations", 4))
        self.model_name = str(self.config.get("model_name", "openai/gpt-4o-mini"))
        self.temperature = float(self.config.get("temperature", 0.0))
        self.llm_factory = llm_factory
        self.audit_evaluator = AuditModeEvaluator(self._synthesis_llm)
        self._tool_map: dict[str, Any] = {
            "pageindex_navigate": self.pageindex_service.navigate,
            "semantic_search": self.semantic_service.search,
            "structured_query": self.structured_service.query,
        }
        self._tool_specs = [
            self.pageindex_service.build_tool(),
            self.semantic_service.build_tool(),
            self.structured_service.build_tool(),
        ]

    def query(self, state: GraphState, request: QueryRequest) -> QueryResult:
        result = self._run_runtime(state, request)
        final = result.get("final_result")
        if final is None:
            raise QueryAgentError(str(result.get("query_error") or "query_agent_failed"))
        return final

    def query_node(self, state: GraphState) -> GraphState:
        if state.query_request is None:
            return state.model_copy(
                update={
                    "query_result": None,
                    "query_error": "missing_query_request",
                    "query_meta": {"rule_version": self._rule_version()},
                }
            )
        try:
            runtime = self._run_runtime(state, state.query_request)
        except (QueryStageError, QueryAgentError) as exc:
            return state.model_copy(
                update={
                    "query_result": None,
                    "query_error": str(exc),
                    "query_meta": {"rule_version": self._rule_version(), "status": "failed_closed"},
                }
            )
        final = runtime.get("final_result")
        if final is None:
            return state.model_copy(
                update={
                    "query_result": None,
                    "query_error": str(runtime.get("query_error") or "query_agent_failed"),
                    "query_meta": {"rule_version": self._rule_version(), "status": "failed_closed"},
                }
            )
        return state.model_copy(
            update={
                "query_result": final,
                "query_error": None,
                "query_messages": [self._serialize_message(message) for message in runtime["messages"]],
                "navigation_candidates": runtime["navigation_candidates"],
                "semantic_hits": runtime["semantic_hits"],
                "structured_rows": runtime["structured_rows"],
                "query_meta": {
                    "rule_version": self._rule_version(),
                    "status": "validated",
                    "retrieval_path_used": final.retrieval_path_used,
                    "matched_section_ids": final.matched_section_ids,
                    "matched_fact_ids": final.matched_fact_ids,
                },
            }
        )

    def _run_runtime(self, state: GraphState, request: QueryRequest) -> _QueryRuntimeState:
        runtime = self._prepare_runtime(state, request)
        graph = self._build_graph()
        return graph.invoke(runtime)

    def _prepare_runtime(self, state: GraphState, request: QueryRequest) -> _QueryRuntimeState:
        doc_name = self._document_name(state)
        if state.page_index is not None:
            self.pageindex_service.set_runtime_page_index(state.page_index)
        if state.chunked_document:
            self.semantic_service.set_runtime_chunks(state.doc_id, state.chunked_document)
            self.fact_extractor.extract_and_store(state.doc_id, state.chunked_document, document_name=doc_name)
        preferred = request.preferred_retrieval_path or self._determine_preferred_path(request.user_query)
        if request.preferred_retrieval_path is None:
            request = request.model_copy(update={"preferred_retrieval_path": preferred})
        messages = [
            SystemMessage(content=self._system_prompt(request)),
            HumanMessage(content=f"Document ID: {request.doc_id}\nQuestion: {request.user_query}"),
        ]
        return {
            "query_request": request,
            "doc_name": doc_name,
            "messages": messages,
            "retrieval_path_used": [],
            "navigation_candidates": [],
            "semantic_hits": [],
            "structured_rows": [],
            "final_result": None,
            "query_error": None,
            "step_count": 0,
        }

    def _build_graph(self):
        from langgraph.graph import END, StateGraph

        graph = StateGraph(_QueryRuntimeState)
        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", self._tools_node)
        graph.add_node("finalize", self._finalize_node)
        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {"tools": "tools", "finalize": "finalize"},
        )
        graph.add_edge("tools", "agent")
        graph.add_edge("finalize", END)
        return graph.compile()

    def _agent_node(self, state: _QueryRuntimeState) -> dict[str, Any]:
        llm = self._tool_llm()
        response = llm.invoke(state["messages"])
        return {"messages": [*state["messages"], response], "step_count": state["step_count"] + 1}

    def _route_after_agent(self, state: _QueryRuntimeState) -> str:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls and state["step_count"] <= self.max_iterations:
            return "tools"
        return "finalize"

    def _tools_node(self, state: _QueryRuntimeState) -> dict[str, Any]:
        last = state["messages"][-1]
        if not isinstance(last, AIMessage):
            raise QueryAgentError("query_agent_failed")
        messages = list(state["messages"])
        retrieval_path_used = list(state["retrieval_path_used"])
        navigation_candidates = list(state["navigation_candidates"])
        semantic_hits = list(state["semantic_hits"])
        structured_rows = list(state["structured_rows"])
        for tool_call in last.tool_calls:
            name = str(tool_call["name"])
            args = tool_call.get("args", {}) or {}
            if name not in self._tool_map:
                raise QueryAgentError("query_agent_failed")
            raw_result = self._tool_map[name](**args)
            if name == "pageindex_navigate":
                normalized = raw_result if isinstance(raw_result, PageIndexNavigationResult) else PageIndexNavigationResult.model_validate(raw_result)
                navigation_candidates.append(normalized)
            elif name == "semantic_search":
                normalized_search = raw_result if isinstance(raw_result, SemanticSearchResult) else SemanticSearchResult.model_validate(raw_result)
                semantic_hits.extend(normalized_search.hits)
                raw_result = normalized_search
            elif name == "structured_query":
                normalized_query = raw_result if isinstance(raw_result, StructuredQueryResult) else StructuredQueryResult.model_validate(raw_result)
                structured_rows.extend(normalized_query.rows)
                raw_result = normalized_query
            if name not in retrieval_path_used:
                retrieval_path_used.append(name)
            messages.append(
                ToolMessage(
                    content=json.dumps(raw_result.model_dump(mode="json"), sort_keys=True),
                    tool_call_id=str(tool_call["id"]),
                    name=name,
                )
            )
        return {
            "messages": messages,
            "retrieval_path_used": retrieval_path_used,
            "navigation_candidates": navigation_candidates,
            "semantic_hits": self._dedupe_semantic_hits(semantic_hits),
            "structured_rows": self._dedupe_structured_rows(structured_rows),
        }

    def _finalize_node(self, state: _QueryRuntimeState) -> dict[str, Any]:
        request = state["query_request"]
        provenance_by_id = self._provenance_index(state["doc_name"], state["semantic_hits"], state["structured_rows"])
        retrieval_path_used = [path for path in state["retrieval_path_used"] if path in self._tool_map]
        if request.mode == "audit":
            audit = self.audit_evaluator.evaluate(
                request,
                retrieval_path_used or [request.preferred_retrieval_path or "pageindex_navigate"],
                state["semantic_hits"],
                state["structured_rows"],
                provenance_by_id,
            )
            final = QueryResult(
                answer=audit.explanation,
                provenance_chain=audit.provenance_chain,
                support_status=audit.support_status,
                retrieval_path_used=audit.retrieval_path_used,
                matched_section_ids=sorted({item.section_id for item in audit.provenance_chain if item.section_id}),
                matched_fact_ids=sorted({item.fact_id for item in audit.provenance_chain if item.fact_id}),
                metadata={"mode": "audit", **audit.metadata},
            )
            return {"final_result": final}
        if not state["semantic_hits"] and not state["structured_rows"]:
            result = QueryResult(
                answer="No supporting evidence was found for this question in the available document artifacts.",
                provenance_chain=[],
                support_status="not_found",
                retrieval_path_used=retrieval_path_used or [request.preferred_retrieval_path or "pageindex_navigate"],
                matched_section_ids=[],
                matched_fact_ids=[],
                metadata={"mode": request.mode, "reason": "no_evidence"},
            )
            return {"final_result": result}
        draft = self._draft_answer(request, state)
        evidence_ids = [*draft.cited_chunk_ids, *draft.cited_fact_ids]
        provenance = [provenance_by_id[evidence_id] for evidence_id in evidence_ids if evidence_id in provenance_by_id]
        result = QueryResult(
            answer=draft.answer,
            provenance_chain=provenance,
            support_status=draft.support_status,
            retrieval_path_used=retrieval_path_used or [request.preferred_retrieval_path or "pageindex_navigate"],
            matched_section_ids=sorted({item.section_id for item in provenance if item.section_id}),
            matched_fact_ids=sorted({item.fact_id for item in provenance if item.fact_id}),
            metadata={
                "mode": request.mode,
                "cited_chunk_ids": draft.cited_chunk_ids,
                "cited_fact_ids": draft.cited_fact_ids,
            },
        )
        return {"final_result": result}

    def _draft_answer(self, request: QueryRequest, state: _QueryRuntimeState) -> QueryAnswerDraft:
        llm = self._synthesis_llm()
        messages = [
            (
                "system",
                "You answer questions using only supplied evidence. Return support_status supported, not_found, or unverifiable. Cite only the supplied chunk and fact IDs. If support_status is supported, cite evidence IDs.",
            ),
            (
                "human",
                self._render_answer_prompt(request, state["navigation_candidates"], state["semantic_hits"], state["structured_rows"]),
            ),
        ]
        try:
            draft = llm.with_structured_output(QueryAnswerDraft).invoke(messages)
        except Exception as exc:  # pragma: no cover
            raise QueryAgentError("query_agent_failed") from exc
        if isinstance(draft, dict):
            draft = QueryAnswerDraft.model_validate(draft)
        return draft

    def _tool_llm(self) -> Any:
        llm = self._base_llm()
        return llm.bind_tools(self._tool_specs)

    def _synthesis_llm(self) -> Any:
        return self._base_llm()

    def _base_llm(self) -> Any:
        if self.llm_factory:
            return self.llm_factory()
        ensure_env_loaded()
        try:
            from langchain_openrouter import ChatOpenRouter
        except ImportError as exc:  # pragma: no cover
            raise QueryAgentError("query_agent_failed") from exc
        return ChatOpenRouter(model=self.model_name, temperature=self.temperature)

    @staticmethod
    def _determine_preferred_path(user_query: str) -> RetrievalToolName:
        if FACT_HEAVY_RE.search(user_query) or any(char.isdigit() for char in user_query):
            return "structured_query"
        if SECTION_RE.search(user_query):
            return "pageindex_navigate"
        return "pageindex_navigate"

    def _system_prompt(self, request: QueryRequest) -> str:
        preferred = request.preferred_retrieval_path or self._determine_preferred_path(request.user_query)
        return (
            "You are the Stage 5 Query Agent. You may use exactly three tools: "
            "pageindex_navigate, semantic_search, and structured_query. "
            "Follow deterministic routing preferences supplied outside the model. "
            f"Preferred first tool: {preferred}. "
            "Use pageindex_navigate first for broad or section-oriented questions, use semantic_search for narrative evidence retrieval, and use structured_query for precise numerical or fact-heavy questions. "
            "Do not answer from memory; gather evidence first."
        )

    @staticmethod
    def _render_answer_prompt(
        request: QueryRequest,
        navigation_candidates: list[PageIndexNavigationResult],
        semantic_hits: list[SemanticSearchHit],
        structured_rows: list[StructuredQueryRow],
    ) -> str:
        sections = []
        for result in navigation_candidates[-2:]:
            for hit in result.matched_sections[:5]:
                sections.append(f"Section {hit.section_id}: {hit.title} (pages {hit.page_start}-{hit.page_end})")
        semantic_block = "\n\n".join(
            f"Chunk {hit.chunk_id} (pages {','.join(str(page) for page in hit.page_refs)}):\n{hit.content}"
            for hit in semantic_hits[:8]
        )
        structured_block = "\n".join(
            f"Fact {row.fact_id}: {row.fact_name} = {row.fact_value}"
            for row in structured_rows[:8]
        )
        return (
            f"Question: {request.user_query}\n"
            f"Mode: {request.mode}\n"
            f"Preferred retrieval path: {request.preferred_retrieval_path}\n\n"
            f"Navigation Candidates:\n{'\n'.join(sections) or 'None'}\n\n"
            f"Semantic Evidence:\n{semantic_block or 'None'}\n\n"
            f"Structured Facts:\n{structured_block or 'None'}\n\n"
            "Return a grounded answer draft."
        )

    @staticmethod
    def _dedupe_semantic_hits(hits: list[SemanticSearchHit]) -> list[SemanticSearchHit]:
        deduped: dict[str, SemanticSearchHit] = {}
        for hit in hits:
            if hit.chunk_id not in deduped or hit.score > deduped[hit.chunk_id].score:
                deduped[hit.chunk_id] = hit
        return list(deduped.values())

    @staticmethod
    def _dedupe_structured_rows(rows: list[StructuredQueryRow]) -> list[StructuredQueryRow]:
        deduped: dict[str, StructuredQueryRow] = {}
        for row in rows:
            if row.fact_id not in deduped or row.score > deduped[row.fact_id].score:
                deduped[row.fact_id] = row
        return list(deduped.values())

    @staticmethod
    def _provenance_index(
        doc_name: str,
        semantic_hits: list[SemanticSearchHit],
        structured_rows: list[StructuredQueryRow],
    ) -> dict[str, ProvenanceChainItem]:
        provenance: dict[str, ProvenanceChainItem] = {}
        for hit in semantic_hits:
            provenance[hit.chunk_id] = ProvenanceChainItem(
                document_name=doc_name,
                page_number=min(hit.page_refs),
                bounding_box=hit.bounding_box,
                content_hash=hit.content_hash,
                chunk_id=hit.chunk_id,
                section_id=hit.section_id,
            )
        for row in structured_rows:
            provenance[row.fact_id] = ProvenanceChainItem(
                document_name=row.document_name,
                page_number=row.page_number,
                bounding_box=row.bounding_box,
                content_hash=row.content_hash,
                chunk_id=row.source_chunk_id,
                section_id=row.section_id,
                fact_id=row.fact_id,
            )
        return provenance

    @staticmethod
    def _document_name(state: GraphState) -> str:
        if state.page_index is not None and state.page_index.doc_id:
            return state.page_index.doc_id
        return state.doc_id

    def _rule_version(self) -> str:
        return str(self.config.get("rule_version", "query-v1"))

    @staticmethod
    def _serialize_message(message: Any) -> dict[str, Any]:
        if hasattr(message, "model_dump"):
            return message.model_dump(mode="json")
        return {"type": type(message).__name__, "content": str(getattr(message, "content", message))}
