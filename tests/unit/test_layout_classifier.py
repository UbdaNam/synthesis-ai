from synthesis_ai.models.document_profile import LayoutComplexity, OriginType
from synthesis_ai.triage.layout_classifier import LayoutClassifier
from synthesis_ai.triage.pdf_stats_analyzer import PDFStats


def make_stats(image_ratio: float, clusters: float, grid: float, chars: int = 100) -> PDFStats:
    return PDFStats(
        character_count_per_page=[chars],
        character_density=[0.001],
        image_area_ratio=[image_ratio],
        font_metadata_presence=[True],
        bounding_box_distribution={"x_cluster_count": clusters, "grid_alignment_score": grid},
        has_acroform=False,
        extracted_text="sample",
    )


def test_layout_multi_column() -> None:
    stats = make_stats(0.1, clusters=3.0, grid=0.0)
    assert LayoutClassifier().classify(stats, OriginType.NATIVE_DIGITAL) == LayoutComplexity.MULTI_COLUMN


def test_layout_table_heavy() -> None:
    stats = make_stats(0.1, clusters=1.0, grid=0.5)
    assert LayoutClassifier().classify(stats, OriginType.NATIVE_DIGITAL) == LayoutComplexity.TABLE_HEAVY


def test_layout_figure_heavy() -> None:
    stats = make_stats(0.8, clusters=1.0, grid=0.1, chars=30)
    assert LayoutClassifier().classify(stats, OriginType.SCANNED_IMAGE) == LayoutComplexity.FIGURE_HEAVY

