from src.chunking.engine import ChunkingEngine
from tests.unit._stage3_test_utils import make_extracted_document


def test_figure_chunk_keeps_caption_in_metadata():
    engine = ChunkingEngine({})
    chunks = engine.chunk_document(make_extracted_document())
    figure_chunk = next(chunk for chunk in chunks if chunk.chunk_type == "figure")
    assert figure_chunk.metadata["caption"] == "Performance chart"
