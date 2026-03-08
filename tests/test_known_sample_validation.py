from src.agents.triage import OriginClassifier, PDFStatsSummary


def _summary(**overrides):
    baseline = dict(
        total_pages=1,
        total_characters=200,
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
    baseline.update(overrides)
    return PDFStatsSummary(**baseline)


def _config():
    return {
        "triage": {
            "origin_thresholds": {
                "native_char_density_min": 0.002,
                "native_image_ratio_max": 0.20,
                "scanned_char_count_max": 20,
                "scanned_image_ratio_min": 0.60,
            }
        }
    }


def test_known_sample_origin_validation():
    classifier = OriginClassifier()
    samples = [
        (_summary(), "native_digital"),
        (_summary(total_characters=5, avg_char_density=0.0001, avg_image_ratio=0.8, font_metadata_presence=False), "scanned_image"),
        (_summary(total_characters=500, avg_char_density=0.0025, avg_image_ratio=0.7), "mixed"),
        (_summary(acroform_present=True), "form_fillable"),
    ]
    for summary, expected in samples:
        assert classifier.classify(summary, _config()) == expected

