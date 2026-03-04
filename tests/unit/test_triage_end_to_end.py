from synthesis_ai.graph.triage_node import TriageNode
from synthesis_ai.models.graph_state import GraphState
from synthesis_ai.triage.profiling_logger import ProfilingLogger
from tests.unit.test_support import FakeStatsAnalyzer, sample_stats


def test_stage1_end_to_end_profile_and_ledger(tmp_path) -> None:
    profile_dir = tmp_path / "profiles"
    ledger = tmp_path / "profiling_ledger.jsonl"

    from synthesis_ai.triage.profile_repository import ProfileRepository

    node = TriageNode(
        stats_analyzer=FakeStatsAnalyzer(sample_stats(text="api module architecture")),
        profile_repository=ProfileRepository(base_dir=str(profile_dir)),
        profiling_logger=ProfilingLogger(str(ledger)),
    )
    out = node(GraphState(doc_id="doc-e2e", file_path="unused.pdf"))
    assert out.document_profile is not None
    assert (profile_dir / "doc-e2e.json").exists()
    assert ledger.exists()

