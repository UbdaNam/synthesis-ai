from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_structured_fact_path_returns_exact_fact(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="What is the reported revenue?"))
    assert result.support_status == "supported"
    assert result.matched_fact_ids
    assert result.retrieval_path_used[0] == "structured_query"
