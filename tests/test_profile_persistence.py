import json

from src.agents.triage import PDFStatsSummary, TriageAgent
from src.models.graph_state import GraphState


class _StubAnalyzer:
    def analyze(self, file_path: str):
        return PDFStatsSummary(
            total_pages=1,
            total_characters=100,
            avg_char_density=0.003,
            avg_image_ratio=0.1,
            font_metadata_presence=True,
            max_x_clusters=1,
            table_grid_score=0.1,
            figure_ratio=0.1,
            extracted_text="api module protocol",
            layout_signals_used={"max_x_clusters": 1.0, "table_grid_score": 0.1, "figure_ratio": 0.1},
            acroform_present=False,
        )


def test_profile_persistence_is_idempotent(temp_config, workspace_tmp):
    profiles_dir = workspace_tmp / "profiles"
    ledger = workspace_tmp / "profiling_ledger.jsonl"
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(profiles_dir),
        profiling_ledger_path=str(ledger),
        analyzer=_StubAnalyzer(),
        timer=lambda: 1.0,
    )
    state = GraphState(doc_id="doc-1", file_path="sample.pdf")
    agent.triage_node(state)
    agent.triage_node(state)

    profile_path = profiles_dir / "doc-1.json"
    assert profile_path.exists()
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    assert data["doc_id"] == "doc-1"

