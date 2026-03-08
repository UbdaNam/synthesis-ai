from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


def test_extraction_fail_closed_unreadable(temp_config, workspace_tmp):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    profile = DocumentProfile(
        doc_id="doc-missing",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    out = router.extract_node(GraphState(doc_id="doc-missing", file_path="does-not-exist.pdf", document_profile=profile))
    assert out.extracted_document is None
    assert out.extraction_error in {"all_strategies_below_threshold", "budget_cap_exceeded"}
