from tests.unit._stage4_test_utils import make_graph_state, make_indexing_agent


def test_pageindex_section_narrowing_returns_ranked_candidates(workspace_tmp):
    agent = make_indexing_agent(workspace_tmp)
    out = agent.index_node(make_graph_state())
    candidates = agent.rank_sections_for_topic("Acme margin", out.page_index)
    assert candidates
    assert candidates[0].matched_terms
