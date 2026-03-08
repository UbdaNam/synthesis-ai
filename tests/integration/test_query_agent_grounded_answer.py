from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_grounded_answer_returns_provenance(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="What does the report say about financial results?"))
    assert result.support_status == "supported"
    assert result.provenance_chain
    assert "semantic_search" in result.retrieval_path_used
