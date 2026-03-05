from src.graph.triage_node import TriageNode
from src.models.graph_state import GraphState
from src.agents.triage.profiling_logger import ProfilingLogger
from tests.unit.test_support import FakeStatsAnalyzer, sample_stats


def test_repeat_run_same_input_identical_profile(tmp_path) -> None:
    stats = sample_stats(text="deterministic sample text")
    node = TriageNode(
        stats_analyzer=FakeStatsAnalyzer(stats),
        profiling_logger=ProfilingLogger(str(tmp_path / "ledger.jsonl")),
    )
    state = GraphState(doc_id="doc-det", file_path="unused.pdf")
    out1 = node(state)
    out2 = node(state)
    p1 = out1.document_profile.model_dump(exclude={"created_at"})
    p2 = out2.document_profile.model_dump(exclude={"created_at"})
    assert p1 == p2

