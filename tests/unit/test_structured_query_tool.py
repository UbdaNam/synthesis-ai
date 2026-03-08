from src.query.tools.structured_query import StructuredQueryService
from tests.unit._stage5_test_utils import build_stage5_state


def test_structured_query_returns_fact_rows(workspace_tmp):
    state, rules = build_stage5_state(workspace_tmp)
    service = StructuredQueryService(rules)
    result = service.query(state.doc_id, "What is the revenue?", limit=3)
    assert result.rows
    assert result.rows[0].fact_name
    assert result.rows[0].content_hash
