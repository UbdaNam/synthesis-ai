from tests.unit._stage5_test_utils import TestSemanticSearchService, build_stage5_state


def test_semantic_search_returns_hits_with_provenance(workspace_tmp):
    state, rules = build_stage5_state(workspace_tmp)
    service = TestSemanticSearchService(rules)
    service.set_runtime_chunks(state.doc_id, state.chunked_document)
    result = service.search(state.doc_id, "financial results revenue", section_ids=[f"{state.doc_id}-financial-results"], limit=2)
    assert result.hits
    assert result.hits[0].content_hash
    assert result.hits[0].bounding_box.x1 == 100
