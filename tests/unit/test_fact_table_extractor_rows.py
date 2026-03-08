from src.query.fact_table_extractor import FactTableExtractor
from tests.unit._stage5_test_utils import build_stage5_state


def test_fact_table_extractor_extracts_revenue_rows(workspace_tmp):
    state, rules = build_stage5_state(workspace_tmp)
    extractor = FactTableExtractor(rules)
    facts = extractor.extract_facts(state.doc_id, state.chunked_document, document_name=state.doc_id)
    assert any("revenue" in fact.normalized_name for fact in facts)
