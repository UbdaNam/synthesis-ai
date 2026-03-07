import pytest
from pydantic import ValidationError

from src.models.extracted_document import BoundingBox, ExtractedDocument, TextBlock


def test_extracted_document_requires_non_empty_content():
    with pytest.raises(ValidationError):
        ExtractedDocument(
            doc_id="doc-1",
            strategy_used="fast_text",
            confidence_score=0.8,
            metadata={"page_count": 1},
            text_blocks=[],
            tables=[],
            figures=[],
        )


def test_extracted_document_schema_validity():
    doc = ExtractedDocument(
        doc_id="doc-1",
        strategy_used="fast_text",
        confidence_score=0.8,
        metadata={"page_count": 1},
        text_blocks=[
            TextBlock(
                id="tb1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                reading_order=0,
                block_type="paragraph",
                text="abc",
                content_hash="h",
                confidence=0.8,
            )
        ],
        tables=[],
        figures=[],
    )
    assert doc.metadata["page_count"] == 1
