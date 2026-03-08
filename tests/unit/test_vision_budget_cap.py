from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult


class _FastLow(BaseExtractionStrategy):
    name = "fast_text"

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("fast_text", 0.1, None, 0.001)


class _LayoutLow(BaseExtractionStrategy):
    name = "layout_aware"

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("layout_aware", 0.1, None, 0.01)


class _VisionHighCost(BaseExtractionStrategy):
    name = "vision"

    def estimate_tokens(self, page_count, rules):
        return 100000

    def estimate_cost(self, usage_tokens, rules):
        return 100.0

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("vision", 1.0, None, 100.0)


def test_vision_budget_cap_enforced(temp_config, workspace_tmp):
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
        strategy_registry={"fast_text": _FastLow(), "layout_aware": _LayoutLow(), "vision": _VisionHighCost()},
    )
    out = router.extract_node(GraphState(doc_id="doc-1", file_path="sample.pdf", document_profile=profile))
    assert out.extraction_error == "budget_cap_exceeded"
