from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from src.agents.query_agent import QueryAgent
from src.models.extracted_document import BoundingBox
from src.models.graph_state import GraphState
from src.models.ldu import LDU
from src.models.page_index import PageIndexDocument, PageIndexNode
from src.models.query_result import AuditDecisionDraft, QueryAnswerDraft
from src.query.chroma_client import create_persistent_client
from src.query import persist_ldu_cache
from src.query.fact_table_extractor import FactTableExtractor
from src.query.tools.pageindex_navigate import PageIndexNavigateService
from src.query.tools.semantic_search import SemanticSearchService
from src.query.tools.structured_query import StructuredQueryService


def make_narrative_ldus(doc_id: str = "doc-1") -> list[LDU]:
    return [
        LDU(
            id=f"{doc_id}-intro",
            doc_id=doc_id,
            content="Acme Corp reported stronger financial results in Q4 with revenue growth across major regions.",
            chunk_type="section_text",
            page_refs=[1],
            bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=20),
            parent_section="Overview",
            token_count=12,
            content_hash="hash-intro",
            metadata={},
        ),
        LDU(
            id=f"{doc_id}-table",
            doc_id=doc_id,
            content="Metric | Value\nRevenue | USD 1250000\nMargin | 32%",
            chunk_type="table",
            page_refs=[2],
            bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=40),
            parent_section="Financial Results",
            token_count=10,
            content_hash="hash-table",
            metadata={"headers": ["Metric", "Value"], "section_id": f"{doc_id}-financial-results"},
        ),
        LDU(
            id=f"{doc_id}-notes",
            doc_id=doc_id,
            content="Notes: Results are unaudited and include regional growth commentary.",
            chunk_type="section_text",
            page_refs=[3],
            bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=15),
            parent_section="Notes",
            token_count=9,
            content_hash="hash-notes",
            metadata={},
        ),
    ]


def make_page_index(doc_id: str = "doc-1") -> PageIndexDocument:
    overview = PageIndexNode(
        id=f"{doc_id}-overview",
        doc_id=doc_id,
        title="Overview",
        page_start=1,
        page_end=1,
        child_sections=[],
        key_entities=["Acme Corp"],
        summary="This section summarizes the document and introduces the financial results.",
        data_types_present=["narrative_text"],
        parent_section_id=f"{doc_id}-root",
        chunk_ids=[f"{doc_id}-intro"],
        metadata={"direct_chunk_ids": [f"{doc_id}-intro"]},
    )
    financial = PageIndexNode(
        id=f"{doc_id}-financial-results",
        doc_id=doc_id,
        title="Financial Results",
        page_start=2,
        page_end=2,
        child_sections=[],
        key_entities=["Revenue"],
        summary="This section contains the main statistics table and revenue figures.",
        data_types_present=["tables"],
        parent_section_id=f"{doc_id}-root",
        chunk_ids=[f"{doc_id}-table"],
        metadata={"direct_chunk_ids": [f"{doc_id}-table"]},
    )
    notes = PageIndexNode(
        id=f"{doc_id}-notes-section",
        doc_id=doc_id,
        title="Notes / Disclaimers",
        page_start=3,
        page_end=3,
        child_sections=[],
        key_entities=[],
        summary="This section captures the notes and disclaimer language.",
        data_types_present=["narrative_text"],
        parent_section_id=f"{doc_id}-root",
        chunk_ids=[f"{doc_id}-notes"],
        metadata={"direct_chunk_ids": [f"{doc_id}-notes"]},
    )
    root = PageIndexNode(
        id=f"{doc_id}-root",
        doc_id=doc_id,
        title="Document",
        page_start=1,
        page_end=3,
        child_sections=[overview, financial, notes],
        key_entities=["Acme Corp"],
        summary="Top-level document node.",
        data_types_present=["narrative_text", "tables"],
        parent_section_id=None,
        chunk_ids=[f"{doc_id}-intro", f"{doc_id}-table", f"{doc_id}-notes"],
        metadata={"direct_chunk_ids": [f"{doc_id}-intro", f"{doc_id}-table", f"{doc_id}-notes"]},
    )
    return PageIndexDocument(
        doc_id=doc_id,
        root_sections=[root],
        section_count=4,
        chunk_count=3,
        artifact_path="",
        rule_version="pageindex-test",
        metadata={"chunk_ids": [f"{doc_id}-intro", f"{doc_id}-table", f"{doc_id}-notes"]},
    )


def persist_page_index(workspace_tmp: Path, document: PageIndexDocument) -> Path:
    target = workspace_tmp / "pageindex"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{document.doc_id}.json"
    path.write_text(json.dumps(document.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


class DeterministicEmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed(text) for text in input]

    def embed_documents(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed(text) for text in input]

    def embed_query(self, input: str | list[str]) -> list[list[float]] | list[float]:  # noqa: A002
        if isinstance(input, list):
            return [self._embed(text) for text in input]
        return self._embed(input)

    @staticmethod
    def _embed(text: str) -> list[float]:
        dims = [0.0] * 8
        for index, token in enumerate(text.lower().split()):
            dims[index % 8] += (sum(ord(ch) for ch in token) % 101) / 100.0
        return dims

    @staticmethod
    def name() -> str:
        return "deterministic_test_embeddings"

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
        return {"name": "deterministic_test_embeddings", "space": "cosine"}


class TestSemanticSearchService(SemanticSearchService):
    def _embedding_function(self) -> Any:
        return DeterministicEmbeddingFunction()


class DeterministicToolCallingModel:
    def __init__(self, schema: Any | None = None) -> None:
        self.schema = schema
        self.tools = []

    def bind_tools(self, tools):
        bound = DeterministicToolCallingModel(self.schema)
        bound.tools = tools
        return bound

    def with_structured_output(self, schema):
        return DeterministicToolCallingModel(schema)

    def invoke(self, messages):
        if self.schema is QueryAnswerDraft:
            prompt = messages[-1][1]
            if "Fact fact-" in prompt:
                fact_id = prompt.split("Fact ", 1)[1].split(":", 1)[0].strip()
                return QueryAnswerDraft(answer="The reported revenue is USD 1250000.", support_status="supported", cited_fact_ids=[fact_id])
            if "Chunk doc-1-intro" in prompt:
                return QueryAnswerDraft(answer="Acme Corp reported stronger Q4 financial results with revenue growth.", support_status="supported", cited_chunk_ids=["doc-1-intro"])
            return QueryAnswerDraft(answer="No grounded answer was found.", support_status="not_found")
        if self.schema is AuditDecisionDraft:
            prompt = messages[-1][1]
            if "Revenue | USD 1250000" in prompt and "1250000" in prompt:
                return AuditDecisionDraft(explanation="The claim is supported by the retrieved revenue fact.", support_status="supported", cited_fact_ids=[prompt.split("Fact ", 1)[1].split(":", 1)[0].strip()])
            if "Semantic Evidence:\nNone" in prompt and "Structured Facts:\nNone" in prompt:
                return AuditDecisionDraft(explanation="No evidence was found for the claim.", support_status="not_found")
            return AuditDecisionDraft(explanation="The available evidence is insufficient to verify the claim.", support_status="unverifiable")

        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        human = next(message for message in messages if getattr(message, "type", "") == "human")
        content = human.content
        doc_id = content.split("Document ID:", 1)[1].splitlines()[0].strip()
        question = content.split("Question:", 1)[1].strip().lower()
        if not tool_messages:
            if any(token in question for token in ["revenue", "amount", "fiscal", "invoice", "margin"]):
                return AIMessage(content="", tool_calls=[{"id": "call-1", "name": "structured_query", "args": {"doc_id": doc_id, "query": question, "fact_filters": [], "limit": 3}}])
            return AIMessage(content="", tool_calls=[{"id": "call-1", "name": "pageindex_navigate", "args": {"doc_id": doc_id, "topic": question, "limit": 3}}])
        last_tool = tool_messages[-1]
        if last_tool.name == "pageindex_navigate":
            payload = json.loads(last_tool.content)
            section_ids = [item["section_id"] for item in payload.get("matched_sections", [])[:2]]
            return AIMessage(content="", tool_calls=[{"id": "call-2", "name": "semantic_search", "args": {"doc_id": doc_id, "query": question, "section_ids": section_ids, "limit": 3}}])
        return AIMessage(content="I have enough evidence.")


def seed_vector_store(workspace_tmp: Path, rules: dict[str, Any], chunks: list[LDU], section_map: dict[str, dict[str, Any]]) -> None:
    persist_dir = workspace_tmp / "chroma"
    client = create_persistent_client(str(persist_dir))
    collection = client.get_or_create_collection(name=rules["query"]["vector_collection_name"], embedding_function=DeterministicEmbeddingFunction())
    collection.upsert(
        ids=[chunk.id for chunk in chunks],
        documents=[chunk.content for chunk in chunks],
        metadatas=[
            {
                "doc_id": chunk.doc_id,
                "section_id": section_map.get(chunk.id, {}).get("section_id", chunk.parent_section or ""),
                "section_title": section_map.get(chunk.id, {}).get("section_title", ""),
                "page_refs": ",".join(str(page) for page in chunk.page_refs),
                "chunk_type": chunk.chunk_type,
                "content_hash": chunk.content_hash,
            }
            for chunk in chunks
        ],
    )


def make_query_rules(workspace_tmp: Path) -> dict[str, Any]:
    return {
        "pageindex": {
            "artifact_dir": str(workspace_tmp / "pageindex"),
            "vector_collection_name": "pageindex-ldus-test",
            "vector_persist_directory": str(workspace_tmp / "chroma"),
            "embedding_model": "test-embedding-model",
            "embedding_base_url": "https://example.invalid",
        },
        "query": {
            "rule_version": "query-test",
            "artifact_dir": str(workspace_tmp / "query"),
            "ldu_cache_dir": str(workspace_tmp / "query" / "ldu_cache"),
            "facts_db_path": str(workspace_tmp / "query" / "facts.db"),
            "model_name": "test-model",
            "temperature": 0.0,
            "max_iterations": 4,
            "vector_collection_name": "pageindex-ldus-test",
            "vector_persist_directory": str(workspace_tmp / "chroma"),
        },
    }


def build_stage5_state(workspace_tmp: Path, doc_id: str = "doc-1") -> tuple[GraphState, dict[str, Any]]:
    rules = make_query_rules(workspace_tmp)
    chunks = make_narrative_ldus(doc_id)
    page_index = make_page_index(doc_id)
    page_index_path = persist_page_index(workspace_tmp, page_index)
    persist_ldu_cache(doc_id, chunks, rules)
    section_map = {
        f"{doc_id}-intro": {"section_id": f"{doc_id}-overview", "section_title": "Overview"},
        f"{doc_id}-table": {"section_id": f"{doc_id}-financial-results", "section_title": "Financial Results"},
        f"{doc_id}-notes": {"section_id": f"{doc_id}-notes-section", "section_title": "Notes / Disclaimers"},
    }
    seed_vector_store(workspace_tmp, rules, chunks, section_map)
    FactTableExtractor(rules).extract_and_store(doc_id, chunks, document_name=doc_id)
    state = GraphState(doc_id=doc_id, file_path="sample.pdf", chunked_document=chunks, page_index=page_index, page_index_path=str(page_index_path))
    return state, rules


def make_query_agent(workspace_tmp: Path) -> tuple[QueryAgent, GraphState, dict[str, Any]]:
    state, rules = build_stage5_state(workspace_tmp)
    config_path = workspace_tmp / "query_rules.yaml"
    config_path.write_text("query: {}\n", encoding="utf-8")
    pageindex_service = PageIndexNavigateService(rules)
    pageindex_service.set_runtime_page_index(state.page_index)
    semantic_service = TestSemanticSearchService(rules)
    semantic_service.set_runtime_chunks(state.doc_id, state.chunked_document)
    structured_service = StructuredQueryService(rules)
    agent = QueryAgent(
        config_path=str(config_path),
        pageindex_service=pageindex_service,
        semantic_service=semantic_service,
        structured_service=structured_service,
        fact_extractor=FactTableExtractor(rules),
        llm_factory=DeterministicToolCallingModel,
    )
    agent.rules = rules
    agent.config = rules["query"]
    return agent, state, rules
