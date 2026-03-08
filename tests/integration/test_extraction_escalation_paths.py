from src.agents.extractor import ExtractionRouter
from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult
from tests.unit._stage2_test_utils import make_doc


class _Low(BaseExtractionStrategy):
    def __init__(self, name: str, conf: float = 0.1):
        self.name = name
        self.conf = conf

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult(self.name, self.conf, None, 0.001)


class _VisionGood(BaseExtractionStrategy):
    name = "vision"

    def extract(self, context: ExtractionContext) -> StrategyResult:
        return StrategyResult("vision", 0.95, make_doc(doc_id=context.doc_id, strategy="vision"), 0.02)


def test_extraction_escalation_paths(temp_config, workspace_tmp):
    router = ExtractionRouter(
        config_path=str(temp_config),
        ledger_path=str(workspace_tmp / "ledger.jsonl"),
        strategy_registry={"fast_text": _Low("fast_text"), "layout_aware": _Low("layout_aware"), "vision": _VisionGood()},
    )
    profile = DocumentProfile(
        doc_id="doc-esc",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    out = router.extract_node(GraphState(doc_id="doc-esc", file_path="sample.pdf", document_profile=profile))
    assert [a.strategy_used for a in out.extraction_attempts] == ["fast_text", "layout_aware", "vision"]
