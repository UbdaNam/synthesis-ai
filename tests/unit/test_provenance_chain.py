from src.models.extracted_document import BoundingBox
from src.models.provenance_chain import ProvenanceChainItem


def test_provenance_chain_requires_source_linkage():
    item = ProvenanceChainItem(
        document_name="doc-1",
        page_number=1,
        bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        content_hash="hash-1",
        chunk_id="chunk-1",
    )
    assert item.chunk_id == "chunk-1"
