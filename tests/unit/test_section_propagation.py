from src.chunking.engine import ChunkingEngine
from tests.unit._stage3_test_utils import make_extracted_document


def test_section_metadata_propagates_to_child_chunks():
    engine = ChunkingEngine({"chunking": {"max_tokens_per_chunk": 50}})
    chunks = engine.chunk_document(make_extracted_document())
    child_chunks = [chunk for chunk in chunks if chunk.chunk_type != "section_header"]
    assert any(chunk.parent_section == "1 Overview" for chunk in child_chunks)
