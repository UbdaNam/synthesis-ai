from tests.unit._stage4_test_utils import make_graph_state, make_indexing_agent


def test_pageindex_vector_ingestion_reports_success(workspace_tmp):
    agent = make_indexing_agent(workspace_tmp)
    out = agent.index_node(make_graph_state())
    assert out.indexing_meta["vector_ingestion"]["enabled"] is True
    assert out.indexing_meta["vector_ingestion"]["ingested_count"] == len(out.chunked_document)
