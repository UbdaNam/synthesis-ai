from src.agents.chunker import SemanticChunkingAgent
from tests.unit._stage3_test_utils import make_graph_state


def test_chunker_end_to_end(temp_config):
    agent = SemanticChunkingAgent(config_path=str(temp_config))
    out = agent.chunk_node(make_graph_state())
    assert out.chunking_error is None
    assert out.chunked_document
    assert all(chunk.content_hash for chunk in out.chunked_document)
