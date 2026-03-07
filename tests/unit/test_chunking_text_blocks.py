from src.chunking.engine import ChunkingEngine
from tests.unit._stage3_test_utils import make_extracted_document


def test_engine_builds_text_chunks():
    engine = ChunkingEngine({"chunking": {"max_tokens_per_chunk": 50}})
    chunks = engine.chunk_document(make_extracted_document())
    text_chunks = [chunk for chunk in chunks if chunk.chunk_type == "section_text"]
    assert text_chunks
    assert all(chunk.content for chunk in text_chunks)
