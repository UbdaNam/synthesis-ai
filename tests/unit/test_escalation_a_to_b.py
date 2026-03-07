from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult
from tests.unit._stage2_test_utils import make_doc


class _LowFast(BaseExtractionStrategy):
    name = "fast_text"

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("fast_text", 0.2, None, 0.001)


class _GoodLayout(BaseExtractionStrategy):
    name = "layout_aware"

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("layout_aware", 0.9, make_doc(strategy="layout_aware"), 0.01)


class _UnusedVision(BaseExtractionStrategy):
    name = "vision"

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("vision", 0.9, make_doc(strategy="vision"), 0.03)


def _state() -> GraphState:
    profile = DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    return GraphState(doc_id="doc-1", file_path="sample.pdf", document_profile=profile)


def test_escalation_from_a_to_b(temp_config, workspace_tmp):
    router = ExtractionRouter(
        config_path=str(temp_config),
        ledger_path=str(workspace_tmp / "ledger.jsonl"),
        strategy_registry={"fast_text": _LowFast(), "layout_aware": _GoodLayout(), "vision": _UnusedVision()},
    )
    out = router.extract_node(_state())
    assert out.extracted_document is not None
    assert out.extracted_document.strategy_used == "layout_aware"
    assert len(out.extraction_attempts) == 2
