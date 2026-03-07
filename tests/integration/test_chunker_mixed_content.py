from src.agents.chunker import SemanticChunkingAgent
from tests.unit._stage3_test_utils import make_graph_state


def test_chunker_preserves_mixed_content_structure(temp_config):
    agent = SemanticChunkingAgent(config_path=str(temp_config))
    out = agent.chunk_node(make_graph_state())
    chunk_types = {chunk.chunk_type for chunk in out.chunked_document}
    assert "section_header" in chunk_types
    assert "section_text" in chunk_types
    assert any(chunk_type in chunk_types for chunk_type in {"table", "table_segment"})
    assert "figure" in chunk_types
    assert any(chunk_type in chunk_types for chunk_type in {"numbered_list", "list_segment"})
