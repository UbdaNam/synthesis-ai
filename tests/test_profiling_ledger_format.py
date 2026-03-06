import json

from src.agents.triage import PDFStatsSummary, TriageAgent
from src.models.graph_state import GraphState


class _StubAnalyzer:
    def analyze(self, file_path: str):
        return PDFStatsSummary(
            total_pages=1,
            total_characters=120,
            avg_char_density=0.002,
            avg_image_ratio=0.05,
            font_metadata_presence=True,
            max_x_clusters=1,
            table_grid_score=0.1,
            figure_ratio=0.05,
            extracted_text="api module contract",
            layout_signals_used={"max_x_clusters": 1.0, "table_grid_score": 0.1, "figure_ratio": 0.05},
            acroform_present=False,
        )


def test_profiling_ledger_jsonl_format(temp_config, workspace_tmp):
    ledger = workspace_tmp / "profiling_ledger.jsonl"
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(ledger),
        analyzer=_StubAnalyzer(),
        timer=lambda: 2.0,
    )
    agent.triage_node(GraphState(doc_id="doc-ledger", file_path="sample.pdf"))
    line = ledger.read_text(encoding="utf-8").strip().splitlines()[0]
    parsed = json.loads(line)
    assert parsed["doc_id"] == "doc-ledger"
    assert isinstance(parsed["layout_signals_used"], dict)

