from __future__ import annotations

from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.extracted_document import BoundingBox, ExtractedDocument, FigureBlock, StructuredTable, TextBlock
from src.models.graph_state import GraphState


def make_profile(doc_id: str = "doc-1") -> DocumentProfile:
    return DocumentProfile(
        doc_id=doc_id,
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.95),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )


def make_extracted_document(doc_id: str = "doc-1") -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=doc_id,
        strategy_used="layout_aware",
        confidence_score=0.9,
        metadata={"page_count": 2},
        text_blocks=[
            TextBlock(
                id="h1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=10),
                reading_order=0,
                block_type="heading",
                text="1 Overview",
                content_hash="hash-h1",
                confidence=0.9,
            ),
            TextBlock(
                id="p1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=12, x1=100, y1=30),
                reading_order=1,
                block_type="paragraph",
                text="This section summarizes the report and introduces Table 1.",
                content_hash="hash-p1",
                confidence=0.9,
            ),
            TextBlock(
                id="l1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=32, x1=100, y1=38),
                reading_order=2,
                block_type="list_item",
                text="1. First numbered item",
                content_hash="hash-l1",
                confidence=0.9,
            ),
            TextBlock(
                id="l2",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=39, x1=100, y1=45),
                reading_order=3,
                block_type="list_item",
                text="2. Second numbered item",
                content_hash="hash-l2",
                confidence=0.9,
            ),
            TextBlock(
                id="p2",
                page_number=2,
                bounding_box=BoundingBox(x0=0, y0=0, x1=100, y1=18),
                reading_order=4,
                block_type="paragraph",
                text="Refer to Figure 1 and Section 1 for context.",
                content_hash="hash-p2",
                confidence=0.9,
            ),
        ],
        tables=[
            StructuredTable(
                id="t1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=46, x1=100, y1=80),
                caption="Summary table",
                headers=["Metric", "Value"],
                rows=[["Revenue", "10"], ["Profit", "5"], ["Margin", "50%"]],
                content_hash="hash-t1",
                confidence=0.9,
            )
        ],
        figures=[
            FigureBlock(
                id="f1",
                page_number=2,
                bounding_box=BoundingBox(x0=0, y0=20, x1=100, y1=60),
                caption="Performance chart",
                figure_type="chart",
                content_hash="hash-f1",
                confidence=0.9,
            )
        ],
    )


def make_graph_state(doc_id: str = "doc-1") -> GraphState:
    return GraphState(
        doc_id=doc_id,
        file_path="sample_files/background-checks.pdf",
        document_profile=make_profile(doc_id),
        extracted_document=make_extracted_document(doc_id),
    )
