from src.agents.triage import PDFStatsSummary, TriageAgent
from src.graph.graph import build_graph
from src.models.graph_state import GraphState


class _StubAnalyzer:
    def analyze(self, file_path: str):
        return PDFStatsSummary(
            total_pages=1,
            total_characters=210,
            avg_char_density=0.004,
            avg_image_ratio=0.05,
            font_metadata_presence=True,
            max_x_clusters=1,
            table_grid_score=0.1,
            figure_ratio=0.05,
            extracted_text="technical api module",
            layout_signals_used={"max_x_clusters": 1.0, "table_grid_score": 0.1, "figure_ratio": 0.05},
            acroform_present=False,
        )


def test_triage_smoke(temp_config, workspace_tmp):
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(workspace_tmp / "profiling_ledger.jsonl"),
        analyzer=_StubAnalyzer(),
        timer=lambda: 5.0,
    )
    graph = build_graph(agent=agent)
    output = GraphState.model_validate(
        graph.invoke(GraphState(doc_id="doc-smoke", file_path="sample.pdf"))
    )
    assert output.document_profile is not None
    assert output.document_profile.doc_id == "doc-smoke"
    assert (workspace_tmp / "profiles" / "doc-smoke.json").exists()
    assert (workspace_tmp / "profiling_ledger.jsonl").exists()

