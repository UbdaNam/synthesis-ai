import pytest

from src.chunking.engine import ChunkingEngine
from src.chunking.validator import ChunkValidationError, ChunkValidator
from tests.unit._stage3_test_utils import make_extracted_document


def test_chunk_validator_rejects_missing_table_headers():
    engine = ChunkingEngine({})
    chunks = engine.chunk_document(make_extracted_document())
    table_chunk = next(chunk for chunk in chunks if chunk.chunk_type in {"table", "table_segment"})
    table_chunk.metadata["headers"] = []
    with pytest.raises(ChunkValidationError):
        ChunkValidator().validate(chunks)


def test_chunk_validator_rejects_missing_figure_caption_metadata():
    engine = ChunkingEngine({})
    chunks = engine.chunk_document(make_extracted_document())
    figure_chunk = next(chunk for chunk in chunks if chunk.chunk_type == "figure")
    figure_chunk.metadata["caption"] = None
    with pytest.raises(ChunkValidationError):
        ChunkValidator().validate(chunks)
