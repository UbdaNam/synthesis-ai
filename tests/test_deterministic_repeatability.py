from src.agents.triage import PDFStatsSummary, TriageAgent


class _StubAnalyzer:
    def analyze(self, file_path: str):
        return PDFStatsSummary(
            total_pages=1,
            total_characters=300,
            avg_char_density=0.003,
            avg_image_ratio=0.10,
            font_metadata_presence=True,
            max_x_clusters=1,
            table_grid_score=0.1,
            figure_ratio=0.1,
            extracted_text="contract clause statute",
            layout_signals_used={"max_x_clusters": 1.0, "table_grid_score": 0.1, "figure_ratio": 0.1},
            acroform_present=False,
        )


def test_same_input_same_profile(temp_config, workspace_tmp):
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(workspace_tmp / "profiling_ledger.jsonl"),
        analyzer=_StubAnalyzer(),
    )
    profile1, _ = agent.profile_document("doc-1", "sample.pdf")
    profile2, _ = agent.profile_document("doc-1", "sample.pdf")
    assert profile1.model_dump() == profile2.model_dump()

