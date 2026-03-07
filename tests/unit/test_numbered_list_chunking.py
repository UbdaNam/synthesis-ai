from src.chunking.engine import ChunkingEngine
from tests.unit._stage3_test_utils import make_extracted_document


def test_numbered_list_remains_single_ldu_when_under_threshold():
    engine = ChunkingEngine({"chunking": {"numbered_list_split_threshold": 50}})
    chunks = engine.chunk_document(make_extracted_document())
    list_chunks = [chunk for chunk in chunks if chunk.chunk_type == "numbered_list"]
    assert len(list_chunks) == 1


def test_numbered_list_splits_with_continuity_metadata_when_over_threshold():
    engine = ChunkingEngine({"chunking": {"numbered_list_split_threshold": 4}})
    chunks = engine.chunk_document(make_extracted_document())
    list_chunks = [chunk for chunk in chunks if chunk.chunk_type == "list_segment"]
    assert len(list_chunks) == 2
    assert all(chunk.metadata["list_continuation"] for chunk in list_chunks)
