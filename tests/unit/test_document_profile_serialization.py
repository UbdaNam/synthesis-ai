import json

from src.models.document_profile import (
    AnalysisSummary,
    DocumentProfile,
    DomainHint,
    EstimatedExtractionCost,
    LanguageSignal,
    LayoutComplexity,
    OriginType,
)
from src.agents.triage.serialization import serialize_profile_deterministic


def make_profile() -> DocumentProfile:
    return DocumentProfile(
        doc_id="doc-1",
        origin_type=OriginType.NATIVE_DIGITAL,
        layout_complexity=LayoutComplexity.SINGLE_COLUMN,
        language=LanguageSignal(code="en", confidence=0.99),
        domain_hint=DomainHint.TECHNICAL,
        estimated_extraction_cost=EstimatedExtractionCost.FAST_TEXT_SUFFICIENT,
        analysis_summary=AnalysisSummary(
            page_count=1,
            character_count_per_page=[100],
            character_density=[0.01],
            image_area_ratio=[0.0],
            font_metadata_presence=[True],
            bounding_box_distribution={"x_cluster_count": 1.0, "grid_alignment_score": 0.0},
        ),
        created_at="2026-03-04T00:00:00Z",
        deterministic_version="triage-v1",
    )


def test_profile_serialization_consistency() -> None:
    payload_1 = serialize_profile_deterministic(make_profile())
    payload_2 = serialize_profile_deterministic(make_profile())
    assert payload_1 == payload_2
    assert json.loads(payload_1)["doc_id"] == "doc-1"

