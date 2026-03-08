from src.models.query_result import QueryRequest
from tests.unit._stage5_test_utils import make_query_agent


def test_query_agent_prefers_section_navigation_for_narrative_questions(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="What does the report say about financial results?"))
    assert result.retrieval_path_used[0] == "pageindex_navigate"


def test_query_agent_prefers_structured_query_for_fact_questions(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, QueryRequest(doc_id=state.doc_id, user_query="What is the reported revenue?"))
    assert result.retrieval_path_used[0] == "structured_query"
