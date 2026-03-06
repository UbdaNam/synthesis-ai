from src.agents.triage import ExtractionCostResolver, requires_advanced_processing


def test_cost_mapping_native_single():
    resolver = ExtractionCostResolver()
    assert resolver.resolve("native_digital", "single_column") == "fast_text_sufficient"


def test_cost_mapping_scanned_to_vision():
    resolver = ExtractionCostResolver()
    assert resolver.resolve("scanned_image", "single_column") == "needs_vision_model"


def test_cost_mapping_layout_to_layout_model():
    resolver = ExtractionCostResolver()
    assert resolver.resolve("native_digital", "table_heavy") == "needs_layout_model"


def test_sc004_advanced_processing_rule():
    assert requires_advanced_processing("needs_layout_model")
    assert requires_advanced_processing("needs_vision_model")
    assert not requires_advanced_processing("fast_text_sufficient")

