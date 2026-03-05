from src.models.document_profile import OriginType
from src.agents.triage.origin_classifier import OriginClassifier
from src.agents.triage.pdf_stats_analyzer import PDFStats


def _stats(char_count: int, density: float, image_ratio: float) -> PDFStats:
    return PDFStats(
        character_count_per_page=[char_count],
        character_density=[density],
        image_area_ratio=[image_ratio],
        font_metadata_presence=[True],
        bounding_box_distribution={"x_cluster_count": 1.0, "grid_alignment_score": 0.0},
        has_acroform=False,
        extracted_text="routing quality sample",
    )


def test_routing_quality_threshold_for_advanced_docs() -> None:
    # Documents requiring advanced extraction should avoid native_digital routing.
    samples = [
        _stats(0, 0.0, 0.9),
        _stats(10, 0.0001, 0.8),
        _stats(20, 0.0002, 0.7),
        _stats(30, 0.0002, 0.65),
    ]
    classifier = OriginClassifier()
    advanced = sum(1 for s in samples if classifier.classify(s) != OriginType.NATIVE_DIGITAL)
    assert advanced / len(samples) >= 0.95

