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
from src.agents.triage.profile_repository import ProfileRepository


def test_profile_repository_saves_json(tmp_path) -> None:
    repo = ProfileRepository(base_dir=str(tmp_path))
    profile = DocumentProfile(
        doc_id="doc-repo",
        origin_type=OriginType.NATIVE_DIGITAL,
        layout_complexity=LayoutComplexity.SINGLE_COLUMN,
        language=LanguageSignal(code="en", confidence=0.8),
        domain_hint=DomainHint.GENERAL,
        estimated_extraction_cost=EstimatedExtractionCost.FAST_TEXT_SUFFICIENT,
        analysis_summary=AnalysisSummary(
            page_count=1,
            character_count_per_page=[1],
            character_density=[0.1],
            image_area_ratio=[0.0],
            font_metadata_presence=[True],
            bounding_box_distribution={"x_cluster_count": 1.0, "grid_alignment_score": 0.0},
        ),
        created_at="2026-03-04T00:00:00Z",
        deterministic_version="triage-v1",
    )
    path = repo.save(profile)
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["doc_id"] == "doc-repo"

