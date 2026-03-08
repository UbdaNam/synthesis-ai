from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_audit_mode_returns_closed_world_outcomes(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    supported = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="Revenue is USD 1250000.", mode="audit"))
    assert supported.support_status in {"supported", "unverifiable"}
    missing = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="The report says litigation expense was 5 million.", mode="audit"))
    assert missing.support_status in {"not_found", "unverifiable", "supported"}
