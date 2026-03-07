from src.agents.chunker import SemanticChunkingAgent
from tests.unit._stage3_test_utils import make_graph_state


def test_chunker_fails_closed_on_invalid_output(temp_config):
    state = make_graph_state()
    state.extracted_document.tables[0].headers = []
    agent = SemanticChunkingAgent(config_path=str(temp_config))
    out = agent.chunk_node(state)
    assert out.chunking_error == "table_header_missing"
    assert out.chunked_document == []
