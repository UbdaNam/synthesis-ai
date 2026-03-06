from src.agents.triage import LayoutClassifier, PDFStatsSummary


def _summary(**overrides):
    data = dict(
        total_pages=2,
        total_characters=1000,
        avg_char_density=0.003,
        avg_image_ratio=0.1,
        font_metadata_presence=True,
        max_x_clusters=1,
        table_grid_score=0.1,
        figure_ratio=0.1,
        extracted_text="sample",
        layout_signals_used={"max_x_clusters": 1.0, "table_grid_score": 0.1, "figure_ratio": 0.1},
        acroform_present=False,
    )
    data.update(overrides)
    return PDFStatsSummary(**data)


def _config():
    return {
        "triage": {
            "layout_thresholds": {
                "multi_column_x_clusters_min": 2,
                "table_grid_score_min": 0.35,
                "figure_heavy_image_ratio_min": 0.45,
            }
        }
    }


def test_layout_single_column():
    assert LayoutClassifier().classify(_summary(), _config()) == "single_column"


def test_layout_multi_column():
    assert LayoutClassifier().classify(_summary(max_x_clusters=2), _config()) == "multi_column"


def test_layout_table_heavy():
    assert LayoutClassifier().classify(_summary(table_grid_score=0.6), _config()) == "table_heavy"


def test_layout_figure_heavy():
    assert LayoutClassifier().classify(_summary(avg_image_ratio=0.6), _config()) == "figure_heavy"


def test_layout_mixed_when_multiple_signals():
    mixed = _summary(max_x_clusters=2, table_grid_score=0.5)
    assert LayoutClassifier().classify(mixed, _config()) == "mixed"

