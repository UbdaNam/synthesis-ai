from synthesis_ai.models.document_profile import OriginType
from synthesis_ai.triage.origin_classifier import OriginClassifier
from synthesis_ai.triage.pdf_stats_analyzer import PDFStats


def _stats(char_count: int, density: float, image_ratio: float, acro: bool = False) -> PDFStats:
    return PDFStats(
        character_count_per_page=[char_count],
        character_density=[density],
        image_area_ratio=[image_ratio],
        font_metadata_presence=[True],
        bounding_box_distribution={"x_cluster_count": 1.0, "grid_alignment_score": 0.0},
        has_acroform=acro,
        extracted_text="known sample",
    )


def test_known_sample_origin_expectations() -> None:
    classifier = OriginClassifier()
    samples = [
        (_stats(2000, 0.003, 0.05), OriginType.NATIVE_DIGITAL),
        (_stats(2, 0.0, 0.85), OriginType.SCANNED_IMAGE),
        (_stats(200, 0.001, 0.40), OriginType.MIXED),
        (_stats(300, 0.003, 0.1, acro=True), OriginType.FORM_FILLABLE),
    ]
    correct = sum(1 for stats, expected in samples if classifier.classify(stats) == expected)
    assert correct == len(samples)

