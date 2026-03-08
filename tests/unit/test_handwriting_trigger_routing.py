from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


def test_handwriting_detection_forces_vision(temp_config, workspace_tmp):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    profile = DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    state = GraphState(doc_id="doc-1", file_path="/tmp/handwriting_scan.pdf", document_profile=profile)
    assert router._resolve_start_strategy(state) == "vision"
