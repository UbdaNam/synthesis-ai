from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_mixed_retrieval_uses_real_infrastructure(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="Summarize the financial results and include the revenue figure."))
    assert result.retrieval_path_used
    assert result.provenance_chain
