from src.chunking.engine import ChunkingEngine
from tests.unit._stage3_test_utils import make_extracted_document


def test_table_chunking_repeats_headers_when_split():
    engine = ChunkingEngine({"chunking": {"table_row_group_limit": 1}})
    chunks = engine.chunk_document(make_extracted_document())
    table_chunks = [chunk for chunk in chunks if chunk.chunk_type == "table_segment"]
    assert len(table_chunks) == 3
    assert all("Metric | Value" in chunk.content for chunk in table_chunks)
