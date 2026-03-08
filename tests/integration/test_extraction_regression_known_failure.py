from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


KNOWN_BAD_FILE = "does-not-exist.pdf"


def test_extraction_regression_known_failure(temp_config, workspace_tmp):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    profile = DocumentProfile(
        doc_id="doc-regress",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    out = router.extract_node(GraphState(doc_id="doc-regress", file_path=KNOWN_BAD_FILE, document_profile=profile))
    assert out.extracted_document is None
    assert out.extraction_error is not None
