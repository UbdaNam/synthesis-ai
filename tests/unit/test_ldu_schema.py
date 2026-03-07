import pytest
from pydantic import ValidationError

from src.models.chunk_relationship import ChunkRelationship
from src.models.extracted_document import BoundingBox
from src.models.ldu import LDU


def test_ldu_schema_validates_required_fields():
    ldu = LDU(
        id="ldu-1",
        doc_id="doc-1",
        content="chunk content",
        chunk_type="section_text",
        page_refs=[1],
        bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        parent_section="Overview",
        token_count=2,
        content_hash="hash",
        relationships=[
            ChunkRelationship(
                id="rel-1",
                doc_id="doc-1",
                source_chunk_id="ldu-1",
                target_chunk_id="ldu-0",
                relationship_type="follows",
                target_label="ldu-0",
                resolved=True,
            )
        ],
        metadata={"source_block_ids": ["b1"]},
    )
    assert ldu.chunk_type == "section_text"


def test_ldu_requires_page_refs():
    with pytest.raises(ValidationError):
        LDU(
            id="ldu-1",
            doc_id="doc-1",
            content="chunk content",
            chunk_type="section_text",
            page_refs=[],
            bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            token_count=2,
            content_hash="hash",
        )
