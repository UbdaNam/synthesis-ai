from tests.unit._stage4_test_utils import make_graph_state, make_indexing_agent


def test_pageindex_section_enrichment_populates_required_fields(workspace_tmp):
    agent = make_indexing_agent(workspace_tmp)
    out = agent.index_node(make_graph_state())
    root = out.page_index.root_sections[0]
    child = root.child_sections[0]
    assert root.summary
    assert child.key_entities
    assert "tables" in child.data_types_present
