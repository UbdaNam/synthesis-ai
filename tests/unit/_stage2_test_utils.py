from __future__ import annotations

from src.models.extracted_document import BoundingBox, ExtractedDocument, TextBlock


def make_doc(doc_id: str = "doc-1", strategy: str = "fast_text", confidence: float = 0.9) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=doc_id,
        strategy_used=strategy,  # type: ignore[arg-type]
        confidence_score=confidence,
        metadata={"page_count": 1},
        text_blocks=[
            TextBlock(
                id="tb-1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=0, x1=10, y1=10),
                reading_order=0,
                block_type="paragraph",
                text="hello",
                content_hash="abc",
                confidence=0.9,
            )
        ],
        tables=[],
        figures=[],
    )
