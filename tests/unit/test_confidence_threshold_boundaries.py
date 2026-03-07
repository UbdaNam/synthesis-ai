from src.agents.extractor import ExtractionRouter


def test_confidence_threshold_boundaries(temp_config, workspace_tmp):
    router = ExtractionRouter(config_path=str(temp_config), ledger_path=str(workspace_tmp / "ledger.jsonl"))
    assert router._threshold("fast_text") == 0.70
    assert router._threshold("layout_aware") == 0.75
    assert router._threshold("vision") == 0.78
