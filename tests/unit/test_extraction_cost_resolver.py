from synthesis_ai.models.document_profile import EstimatedExtractionCost, LayoutComplexity, OriginType
from synthesis_ai.triage.extraction_cost_resolver import ExtractionCostResolver


def test_cost_native_single_column_fast() -> None:
    result = ExtractionCostResolver().resolve(OriginType.NATIVE_DIGITAL, LayoutComplexity.SINGLE_COLUMN)
    assert result == EstimatedExtractionCost.FAST_TEXT_SUFFICIENT


def test_cost_multi_column_layout_model() -> None:
    result = ExtractionCostResolver().resolve(OriginType.NATIVE_DIGITAL, LayoutComplexity.MULTI_COLUMN)
    assert result == EstimatedExtractionCost.NEEDS_LAYOUT_MODEL


def test_cost_scanned_vision_model() -> None:
    result = ExtractionCostResolver().resolve(OriginType.SCANNED_IMAGE, LayoutComplexity.SINGLE_COLUMN)
    assert result == EstimatedExtractionCost.NEEDS_VISION_MODEL

