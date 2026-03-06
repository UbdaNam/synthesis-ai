import json

from src.agents.triage import PDFStatsSummary, TriageAgent
from src.models.graph_state import GraphState


class _StubAnalyzer:
    def analyze(self, file_path: str):
        return PDFStatsSummary(
            total_pages=1,
            total_characters=200,
            avg_char_density=0.004,
            avg_image_ratio=0.2,
            font_metadata_presence=True,
            max_x_clusters=2,
            table_grid_score=0.4,
            figure_ratio=0.2,
            extracted_text="invoice revenue tax",
            layout_signals_used={"max_x_clusters": 2.0, "table_grid_score": 0.4, "figure_ratio": 0.2},
            acroform_present=False,
        )


def test_decision_evidence_contains_required_fields(temp_config, workspace_tmp):
    ledger = workspace_tmp / "profiling_ledger.jsonl"
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(ledger),
        analyzer=_StubAnalyzer(),
        timer=lambda: 1.0,
    )
    agent.triage_node(GraphState(doc_id="doc-evidence", file_path="sample.pdf"))
    row = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
    expected = {
        "doc_id",
        "character_density",
        "image_ratio",
        "font_metadata_presence",
        "layout_signals_used",
        "origin_type",
        "layout_complexity",
        "language_code",
        "language_confidence",
        "domain_hint",
        "estimated_extraction_cost",
        "processing_time",
        "threshold_rule_reference",
    }
    assert expected.issubset(row.keys())

