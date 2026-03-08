from src.agents.triage import TriageAgent


def test_language_detection_english(temp_config, workspace_tmp):
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(workspace_tmp / "profiling_ledger.jsonl"),
    )
    signal = agent.detect_language("This is an example invoice document.")
    assert signal.code in {"en", "und"}
    assert 0.0 <= signal.confidence <= 1.0


def test_language_detection_non_english(temp_config, workspace_tmp):
    agent = TriageAgent(
        config_path=str(temp_config),
        profiles_dir=str(workspace_tmp / "profiles"),
        profiling_ledger_path=str(workspace_tmp / "profiling_ledger.jsonl"),
    )
    signal = agent.detect_language("Este documento contiene información médica del paciente.")
    assert signal.code in {"es", "und"}
    assert 0.0 <= signal.confidence <= 1.0

