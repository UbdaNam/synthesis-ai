from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


def test_extraction_normalization_flow(temp_config, workspace_tmp, stage2_sample_pdf):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    profile = DocumentProfile(
        doc_id="doc-flow",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    out = router.extract_node(GraphState(doc_id="doc-flow", file_path=str(stage2_sample_pdf), document_profile=profile))
    assert out.extracted_document is not None
    assert out.extracted_document.doc_id == "doc-flow"
    assert out.extracted_document.text_blocks
