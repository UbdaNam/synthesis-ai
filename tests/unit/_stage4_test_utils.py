from __future__ import annotations

from pathlib import Path

from src.agents.indexer import PageIndexingAgent
from src.indexing.pageindex_builder import PageIndexBuilder
from src.indexing.section_summarizer import SectionSummarizer
from src.indexing.vector_ingestor import VectorIngestor
from src.models.extracted_document import BoundingBox
from src.models.graph_state import GraphState
from src.models.ldu import LDU
from src.models.page_index import SectionSummaryResult


def make_ldus(doc_id: str = "doc-1") -> list[LDU]:
    return [
        LDU(
            id=f"{doc_id}-section-header-1",
            doc_id=doc_id,
            content="1 Overview",
            chunk_type="section_header",
            page_refs=[1],
            bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=10),
            parent_section=None,
            token_count=2,
            content_hash="hash-h1",
            metadata={"section_label": "Section 1"},
        ),
        LDU(
            id=f"{doc_id}-section-text-1",
            doc_id=doc_id,
            content="Acme Corp prepared the quarterly summary and references TABLE-001.",
            chunk_type="section_text",
            page_refs=[1],
            bounding_box=BoundingBox(x0=0, y0=11, x1=100, y1=25),
            parent_section="1 Overview",
            token_count=9,
            content_hash="hash-p1",
            metadata={},
        ),
        LDU(
            id=f"{doc_id}-section-header-2",
            doc_id=doc_id,
            content="1.1 Financial Results",
            chunk_type="section_header",
            page_refs=[2],
            bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=10),
            parent_section=None,
            token_count=3,
            content_hash="hash-h2",
            metadata={"section_label": "Section 1.1"},
        ),
        LDU(
            id=f"{doc_id}-table-1",
            doc_id=doc_id,
            content="Metric | Value\nRevenue | 10\nMargin | 50%",
            chunk_type="table",
            page_refs=[2],
            bounding_box=BoundingBox(x0=0, y0=11, x1=100, y1=40),
            parent_section="1.1 Financial Results",
            token_count=8,
            content_hash="hash-t1",
            metadata={"headers": ["Metric", "Value"]},
        ),
        LDU(
            id=f"{doc_id}-figure-1",
            doc_id=doc_id,
            content="Performance chart for Q4.",
            chunk_type="figure",
            page_refs=[3],
            bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=35),
            parent_section="1.1 Financial Results",
            token_count=4,
            content_hash="hash-f1",
            metadata={"caption": "Performance chart"},
        ),
        LDU(
            id=f"{doc_id}-list-1",
            doc_id=doc_id,
            content="1. Approve budget\n2. Review margin",
            chunk_type="numbered_list",
            page_refs=[3],
            bounding_box=BoundingBox(x0=0, y0=36, x1=100, y1=55),
            parent_section="1.1 Financial Results",
            token_count=6,
            content_hash="hash-l1",
            metadata={},
        ),
    ]


def make_graph_state(doc_id: str = "doc-1") -> GraphState:
    return GraphState(doc_id=doc_id, file_path="sample_files/background-checks.pdf", chunked_document=make_ldus(doc_id))


class FakeStructuredLLM:
    def invoke(self, messages):
        human = messages[-1][1]
        if "Financial Results" in human:
            return SectionSummaryResult(
                section_id="override",
                summary="This section covers financial results and supporting evidence. It includes tables, figures, and list actions.",
                source_chunk_ids=["doc-1-table-1", "doc-1-figure-1"],
            )
        return SectionSummaryResult(
            section_id="override",
            summary="This section introduces the document scope and principal entities. It frames the context for later sections.",
            source_chunk_ids=["doc-1-section-header-1", "doc-1-section-text-1"],
        )


class FakeLLM:
    def with_structured_output(self, _schema):
        return FakeStructuredLLM()


class FakeCollection:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def upsert(self, *, ids, documents, metadatas):
        for item_id, document, metadata in zip(ids, documents, metadatas, strict=True):
            self.records.append({"id": item_id, "document": document, "metadata": metadata})


class FakeClient:
    def __init__(self) -> None:
        self.collection = FakeCollection()

    def get_or_create_collection(self, *, name, embedding_function):
        self.collection.name = name
        self.collection.embedding_function = embedding_function
        return self.collection


def fake_client_factory(_path: str) -> FakeClient:
    return FakeClient()


class FakeVectorIngestor(VectorIngestor):
    def __init__(self) -> None:
        super().__init__(
            rules={
                "pageindex": {
                    "vector_collection_name": "test",
                    "vector_persist_directory": ".refinery/pageindex/chroma",
                }
            },
            client_factory=fake_client_factory,
        )

    def _embedding_function(self):
        return object()


def make_indexing_agent(tmp_path: Path) -> PageIndexingAgent:
    rules = {
        "pageindex": {
            "artifact_dir": str(tmp_path / "pageindex"),
            "rule_version": "pageindex-test",
            "summary_model_name": "gpt-4o-mini",
            "max_chunks_per_summary_request": 4,
            "summary_temperature": 0.0,
            "vector_collection_name": "test-pageindex",
            "vector_persist_directory": str(tmp_path / "chroma"),
            "entity_extraction_stopwords": ["section", "table", "figure", "document"],
            "entity_max_per_section": 8,
            "enable_vector_ingestion": True,
        }
    }
    summarizer = SectionSummarizer(rules=rules, llm_factory=FakeLLM)
    vector_ingestor = FakeVectorIngestor()
    return PageIndexingAgent(
        builder=PageIndexBuilder(rules),
        entity_extractor=None,
        data_type_detector=None,
        summarizer=summarizer,
        vector_ingestor=vector_ingestor,
        timer=lambda: 100.0,
    )
