import json

from src.agents.triage import PDFStatsSummary, TriageAgent
from src.models.graph_state import GraphState


class _StubAnalyzer:
    def analyze(self, file_path: str):
        return PDFStatsSummary(
            total_pages=1,
            total_characters=250,
            avg_char_density=0.003,
            avg_image_ratio=0.15,
            font_metadata_presence=True,
            max_x_clusters=1,
            table_grid_score=0.2,
            figure_ratio=0.15,
            extracted_text="diagnosis patient treatment",
            layout_signals_used={"max_x_clusters": 1.0, "table_grid_score": 0.2, "figure_ratio": 0.15},
            acroform_present=False,
        )


def test_evidence_is_repeatable_with_deterministic_timer(temp_config, workspace_tmp):
    ticks = [10.0, 10.25, 20.0, 20.25]
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(workspace_tmp / "profiling_ledger.jsonl"),
        analyzer=_StubAnalyzer(),
        timer=lambda: ticks.pop(0),
    )
    state = GraphState(doc_id="doc-repeat", file_path="sample.pdf")
    agent.triage_node(state)
    agent.triage_node(state)
    lines = (workspace_tmp / "profiling_ledger.jsonl").read_text(encoding="utf-8").strip().splitlines()
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first == second

