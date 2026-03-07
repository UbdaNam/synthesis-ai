from src.models.extracted_document import (
    BoundingBox,
    ExtractedDocument,
    ExtractionAttemptRecord,
    ExtractionLedgerEntry,
    FigureBlock,
    StructuredTable,
    TextBlock,
)


def test_stage2_contract_models_validate_required_fields():
    block = TextBlock(
        id="b1",
        page_number=1,
        bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        reading_order=0,
        block_type="paragraph",
        text="hello",
        content_hash="hash",
        confidence=0.9,
    )
    table = StructuredTable(
        id="t1",
        page_number=1,
        bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        headers=["h1"],
        rows=[["v1"]],
        content_hash="hash-t",
        confidence=0.9,
    )
    figure = FigureBlock(
        id="f1",
        page_number=1,
        bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        figure_type="image",
        content_hash="hash-f",
        confidence=0.8,
    )
    doc = ExtractedDocument(
        doc_id="doc-1",
        strategy_used="layout_aware",
        confidence_score=0.85,
        metadata={"page_count": 1},
        text_blocks=[block],
        tables=[table],
        figures=[figure],
    )
    attempt = ExtractionAttemptRecord(
        doc_id="doc-1",
        attempt_index=1,
        strategy_used="layout_aware",
        confidence_score=0.85,
        cost_estimate=0.01,
        usage_tokens=0,
        processing_time=0.1,
        escalated=False,
        rule_reference="extraction-v1",
        final_disposition="accepted",
    )
    ledger = ExtractionLedgerEntry(
        doc_id="doc-1",
        strategy_used="layout_aware",
        confidence_score=0.85,
        cost_estimate=0.01,
        processing_time=0.1,
        escalation_flag=False,
        threshold_rule_reference="extraction-v1",
    )
    assert doc.doc_id == "doc-1"
    assert attempt.attempt_index == 1
    assert ledger.strategy_used == "layout_aware"
