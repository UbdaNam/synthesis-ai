from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_real_infrastructure_uses_pageindex_chroma_and_sqlite(workspace_tmp):
    agent, state, rules = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="What is the reported revenue?"))
    assert (workspace_tmp / "pageindex" / f"{state.doc_id}.json").exists()
    assert (workspace_tmp / "query" / "facts.db").exists()
    assert result.retrieval_path_used
