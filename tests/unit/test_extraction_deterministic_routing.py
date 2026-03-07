from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


def _state(path: str) -> GraphState:
    profile = DocumentProfile(
        doc_id="doc-repeat",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    return GraphState(doc_id="doc-repeat", file_path=path, document_profile=profile)


def test_deterministic_routing(temp_config, workspace_tmp, stage2_sample_pdf):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    out1 = router.extract_node(_state(str(stage2_sample_pdf)))
    out2 = router.extract_node(_state(str(stage2_sample_pdf)))
    attempts1 = [a.strategy_used for a in out1.extraction_attempts]
    attempts2 = [a.strategy_used for a in out2.extraction_attempts]
    assert attempts1 == attempts2
