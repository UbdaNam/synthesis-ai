from src.chunking.engine import ChunkingEngine
from tests.unit._stage3_test_utils import make_extracted_document


def test_cross_references_are_stored_as_relationships():
    engine = ChunkingEngine({})
    chunks = engine.chunk_document(make_extracted_document())
    refs = [rel.relationship_type for chunk in chunks for rel in chunk.relationships]
    assert "references_table" in refs
    assert "references_figure" in refs
    assert "references_section" in refs
