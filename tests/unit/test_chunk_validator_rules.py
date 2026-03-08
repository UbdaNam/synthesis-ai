from src.chunking.engine import ChunkingEngine
from src.chunking.validator import ChunkValidator
from tests.unit._stage3_test_utils import make_extracted_document


def test_chunk_validator_accepts_all_five_rules():
    engine = ChunkingEngine({"chunking": {"table_row_group_limit": 1}})
    chunks = engine.chunk_document(make_extracted_document())
    validated = ChunkValidator().validate(chunks)
    assert validated
