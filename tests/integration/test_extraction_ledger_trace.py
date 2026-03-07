import json

from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState


def test_extraction_ledger_trace(temp_config, workspace_tmp, stage2_sample_pdf):
    ledger = workspace_tmp / "ledger.jsonl"
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(ledger))
    profile = DocumentProfile(
        doc_id="doc-trace",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    _ = router.extract_node(GraphState(doc_id="doc-trace", file_path=str(stage2_sample_pdf), document_profile=profile))
    entries = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert entries
    assert all(e["threshold_rule_reference"] for e in entries)
