from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from models.document_profile import (
    AnalysisSummary,
    DocumentProfile,
    LanguageSignal,
)
from models.graph_state import GraphState
from triage.config import DETERMINISTIC_VERSION
from triage.domain.keyword_strategy import KeywordDomainClassifier
from triage.extraction_cost_resolver import ExtractionCostResolver
from triage.language_detector import LanguageDetector
from triage.layout_classifier import LayoutClassifier
from triage.origin_classifier import OriginClassifier
from triage.pdf_stats_analyzer import PDFStatsAnalyzer
from triage.profile_repository import ProfileRepository
from triage.profiling_ledger_schema import ProfilingLedgerEntry
from triage.profiling_logger import ProfilingLogger


class TriageNode:
    def __init__(
        self,
        stats_analyzer: PDFStatsAnalyzer | None = None,
        origin_classifier: OriginClassifier | None = None,
        layout_classifier: LayoutClassifier | None = None,
        domain_classifier: KeywordDomainClassifier | None = None,
        language_detector: LanguageDetector | None = None,
        cost_resolver: ExtractionCostResolver | None = None,
        profile_repository: ProfileRepository | None = None,
        profiling_logger: ProfilingLogger | None = None,
    ) -> None:
        self.stats_analyzer = stats_analyzer or PDFStatsAnalyzer()
        self.origin_classifier = origin_classifier or OriginClassifier()
        self.layout_classifier = layout_classifier or LayoutClassifier()
        self.domain_classifier = domain_classifier or KeywordDomainClassifier()
        self.language_detector = language_detector or LanguageDetector()
        self.cost_resolver = cost_resolver or ExtractionCostResolver()
        self.profile_repository = profile_repository or ProfileRepository()
        self.profiling_logger = profiling_logger or ProfilingLogger()

    def __call__(self, state: GraphState) -> GraphState:
        start = perf_counter()
        stats = self.stats_analyzer.analyze(state.file_path)
        origin = self.origin_classifier.classify(stats)
        layout = self.layout_classifier.classify(stats, origin)
        domain = self.domain_classifier.classify(stats.extracted_text)
        language_result = self.language_detector.detect(stats.extracted_text)
        language = LanguageSignal(code=language_result.code, confidence=language_result.confidence)
        cost = self.cost_resolver.resolve(origin, layout)

        profile = DocumentProfile(
            doc_id=state.doc_id,
            origin_type=origin,
            layout_complexity=layout,
            language=language,
            domain_hint=domain,
            estimated_extraction_cost=cost,
            analysis_summary=AnalysisSummary(
                page_count=stats.page_count,
                character_count_per_page=stats.character_count_per_page,
                character_density=stats.character_density,
                image_area_ratio=stats.image_area_ratio,
                font_metadata_presence=stats.font_metadata_presence,
                bounding_box_distribution=stats.bounding_box_distribution,
            ),
            created_at=datetime.now(UTC).isoformat(),
            deterministic_version=DETERMINISTIC_VERSION,
        )
        self.profile_repository.save(profile)
        processing_time = perf_counter() - start
        self.profiling_logger.log(
            ProfilingLedgerEntry(
                doc_id=profile.doc_id,
                char_density=stats.character_density,
                image_ratio=stats.image_area_ratio,
                layout_signals=stats.bounding_box_distribution,
                origin_type=profile.origin_type,
                layout_complexity=profile.layout_complexity,
                language=profile.language,
                estimated_extraction_cost=profile.estimated_extraction_cost,
                processing_time=processing_time,
            )
        )
        return GraphState(doc_id=state.doc_id, file_path=state.file_path, document_profile=profile)


def build_stage1_graph() -> object:
    """
    Build a LangGraph pipeline with Stage 1 as the first node.
    Returns compiled graph object when langgraph is installed.
    """
    from langgraph.graph import END, START, StateGraph  # Lazy import for optional runtime.

    graph = StateGraph(GraphState)
    graph.add_node("triage", TriageNode())
    graph.add_edge(START, "triage")
    graph.add_edge("triage", END)
    return graph.compile()

