import json

from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


def test_ledger_metrics_non_negative(temp_config, workspace_tmp, stage2_sample_pdf):
    ledger = workspace_tmp / "ledger.jsonl"
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(ledger))
    profile = DocumentProfile(
        doc_id="doc-metrics",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    _ = router.extract_node(GraphState(doc_id="doc-metrics", file_path=str(stage2_sample_pdf), document_profile=profile))
    entries = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert all(e["processing_time"] >= 0 for e in entries)
    assert all(e["cost_estimate"] >= 0 for e in entries)
