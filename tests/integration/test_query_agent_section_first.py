from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_section_first_path_uses_navigation_before_semantic(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="Which section covers financial results?"))
    assert result.retrieval_path_used[:2] == ["pageindex_navigate", "semantic_search"]
