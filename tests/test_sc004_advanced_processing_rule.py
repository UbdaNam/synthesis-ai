from src.agents.triage import requires_advanced_processing


def test_sc004_advanced_processing_cost_set():
    assert requires_advanced_processing("needs_layout_model")
    assert requires_advanced_processing("needs_vision_model")
    assert not requires_advanced_processing("fast_text_sufficient")

