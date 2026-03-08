from tests.unit._stage4_test_utils import make_graph_state, make_indexing_agent


def test_pageindex_end_to_end_persists_json(workspace_tmp):
    agent = make_indexing_agent(workspace_tmp)
    out = agent.index_node(make_graph_state())
    assert out.page_index is not None
    assert out.page_index_path is not None
    assert (workspace_tmp / "pageindex" / "doc-1.json").exists()
