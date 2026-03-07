from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal


def _profile(origin: str, layout: str, doc_id: str = "doc-1") -> DocumentProfile:
    return DocumentProfile(
        doc_id=doc_id,
        origin_type=origin,  # type: ignore[arg-type]
        layout_complexity=layout,  # type: ignore[arg-type]
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )


def test_initial_strategy_selection_rules(temp_config, workspace_tmp):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    assert router.select_initial_strategy(_profile("native_digital", "single_column")) == "fast_text"
    assert router.select_initial_strategy(_profile("mixed", "single_column")) == "layout_aware"
    assert router.select_initial_strategy(_profile("native_digital", "table_heavy")) == "layout_aware"
    assert router.select_initial_strategy(_profile("scanned_image", "single_column")) == "vision"
