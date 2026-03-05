from src.models.document_profile import OriginType
from src.agents.triage.origin_classifier import OriginClassifier
from src.agents.triage.pdf_stats_analyzer import PDFStats


def build_stats(char_count: int, density: float, image_ratio: float, acroform: bool = False) -> PDFStats:
    return PDFStats(
        character_count_per_page=[char_count],
        character_density=[density],
        image_area_ratio=[image_ratio],
        font_metadata_presence=[True],
        bounding_box_distribution={"x_cluster_count": 1.0, "grid_alignment_score": 0.0},
        has_acroform=acroform,
        extracted_text="sample",
    )


def test_origin_native_digital() -> None:
    assert OriginClassifier().classify(build_stats(2000, 0.003, 0.05)) == OriginType.NATIVE_DIGITAL


def test_origin_scanned_image() -> None:
    assert OriginClassifier().classify(build_stats(0, 0.0, 0.9)) == OriginType.SCANNED_IMAGE


def test_origin_mixed() -> None:
    assert OriginClassifier().classify(build_stats(120, 0.001, 0.4)) == OriginType.MIXED


def test_origin_form_fillable() -> None:
    assert OriginClassifier().classify(build_stats(100, 0.003, 0.1, acroform=True)) == OriginType.FORM_FILLABLE

