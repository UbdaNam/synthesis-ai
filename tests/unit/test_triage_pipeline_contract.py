from src.graph.triage_node import TriageNode
from src.models.graph_state import GraphState
from src.agents.triage.profiling_logger import ProfilingLogger
from tests.unit.test_support import FakeStatsAnalyzer, sample_stats


def test_triage_node_populates_document_profile(tmp_path) -> None:
    node = TriageNode(
        stats_analyzer=FakeStatsAnalyzer(sample_stats()),
        profiling_logger=ProfilingLogger(str(tmp_path / "ledger.jsonl")),
    )
    out = node(GraphState(doc_id="doc-contract", file_path="unused.pdf"))
    assert out.document_profile is not None
    assert out.doc_id == "doc-contract"

