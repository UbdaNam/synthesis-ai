import json
from pathlib import Path

from jsonschema import validate

from synthesis_ai.models.document_profile import (
    AnalysisSummary,
    DocumentProfile,
    DomainHint,
    EstimatedExtractionCost,
    LanguageSignal,
    LayoutComplexity,
    OriginType,
)


def test_document_profile_matches_schema() -> None:
    schema_path = Path("specs/001-triage-document-profile/contracts/document-profile.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    profile = DocumentProfile(
        doc_id="doc-1",
        origin_type=OriginType.NATIVE_DIGITAL,
        layout_complexity=LayoutComplexity.SINGLE_COLUMN,
        language=LanguageSignal(code="en", confidence=0.95),
        domain_hint=DomainHint.GENERAL,
        estimated_extraction_cost=EstimatedExtractionCost.FAST_TEXT_SUFFICIENT,
        analysis_summary=AnalysisSummary(
            page_count=1,
            character_count_per_page=[10],
            character_density=[0.01],
            image_area_ratio=[0.0],
            font_metadata_presence=[True],
            bounding_box_distribution={"x_cluster_count": 1.0, "grid_alignment_score": 0.0},
        ),
        created_at="2026-03-04T00:00:00Z",
        deterministic_version="triage-v1",
    )
    validate(instance=profile.model_dump(mode="json"), schema=schema)

