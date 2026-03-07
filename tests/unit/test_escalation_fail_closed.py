from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult


class _Low(BaseExtractionStrategy):
    def __init__(self, name: str):
        self.name = name

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult(self.name, 0.1, None, 0.001)


def test_fail_closed_after_vision_below_threshold(temp_config, workspace_tmp):
    profile = DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    router = ExtractionRouter(
        config_path=str(temp_config),
        ledger_path=str(workspace_tmp / "ledger.jsonl"),
        strategy_registry={"fast_text": _Low("fast_text"), "layout_aware": _Low("layout_aware"), "vision": _Low("vision")},
    )
    out = router.extract_node(GraphState(doc_id="doc-1", file_path="sample.pdf", document_profile=profile))
    assert out.extracted_document is None
    assert out.extraction_error == "all_strategies_below_threshold"
