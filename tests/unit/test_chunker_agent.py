from src.agents.chunker import SemanticChunkingAgent
from tests.unit._stage3_test_utils import make_graph_state


def test_chunker_agent_updates_state(temp_config):
    agent = SemanticChunkingAgent(config_path=str(temp_config))
    out = agent.chunk_node(make_graph_state())
    assert out.chunking_error is None
    assert out.chunked_document
    assert out.chunk_relationships
    assert out.chunking_meta["validation_status"] == "validated"
