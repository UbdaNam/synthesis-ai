import json

from tests.unit._stage4_test_utils import make_graph_state, make_indexing_agent


def test_pageindex_persistence_regression_contains_required_fields(workspace_tmp):
    agent = make_indexing_agent(workspace_tmp)
    out = agent.index_node(make_graph_state())
    with open(out.page_index_path, "r", encoding="utf-8") as stream:
        persisted = json.load(stream)
    assert persisted["doc_id"] == "doc-1"
    assert persisted["root_sections"][0]["title"] == "1 Overview"
