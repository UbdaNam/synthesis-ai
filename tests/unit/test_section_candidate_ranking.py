from tests.unit._stage4_test_utils import make_graph_state, make_indexing_agent


def test_section_ranking_prefers_matching_section(workspace_tmp):
    agent = make_indexing_agent(workspace_tmp)
    out = agent.index_node(make_graph_state())
    assert out.page_index is not None
    candidates = agent.rank_sections_for_topic("financial margin", out.page_index)
    assert candidates[0].title == "1.1 Financial Results"
    assert candidates[0].score >= candidates[-1].score
