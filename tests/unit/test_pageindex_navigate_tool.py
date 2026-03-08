from src.query.tools.pageindex_navigate import PageIndexNavigateService
from tests.unit._stage5_test_utils import build_stage5_state


def test_pageindex_navigate_ranks_relevant_sections(workspace_tmp):
    state, rules = build_stage5_state(workspace_tmp)
    service = PageIndexNavigateService(rules)
    service.set_runtime_page_index(state.page_index)
    result = service.navigate(state.doc_id, "financial results revenue", limit=2)
    assert result.matched_sections
    assert result.matched_sections[0].title == "Financial Results"
