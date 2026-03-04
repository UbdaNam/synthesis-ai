from synthesis_ai.models.graph_state import GraphState
from synthesis_ai.triage.profiling_logger import ProfilingLogger
from synthesis_ai.graph.triage_node import TriageNode
from tests.unit.test_support import FakeStatsAnalyzer, sample_stats


def test_processing_time_is_recorded(tmp_path) -> None:
    node = TriageNode(
        stats_analyzer=FakeStatsAnalyzer(sample_stats()),
        profiling_logger=ProfilingLogger(str(tmp_path / "profiling_ledger.jsonl")),
    )
    _ = node(GraphState(doc_id="doc-time", file_path="unused.pdf"))
    content = (tmp_path / "profiling_ledger.jsonl").read_text(encoding="utf-8")
    assert "processing_time" in content

