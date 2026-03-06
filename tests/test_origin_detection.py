from src.agents.triage import OriginClassifier, PDFStatsSummary


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
            "origin_thresholds": {
                "native_char_density_min": 0.002,
                "native_image_ratio_max": 0.20,
                "scanned_char_count_max": 20,
                "scanned_image_ratio_min": 0.60,
            }
        }
    }


def test_origin_native_digital():
    classifier = OriginClassifier()
    assert classifier.classify(_summary(), _config()) == "native_digital"


def test_origin_scanned_image():
    classifier = OriginClassifier()
    scanned = _summary(total_characters=10, avg_char_density=0.0001, avg_image_ratio=0.8, font_metadata_presence=False)
    assert classifier.classify(scanned, _config()) == "scanned_image"


def test_origin_mixed():
    classifier = OriginClassifier()
    mixed = _summary(total_characters=500, avg_char_density=0.003, avg_image_ratio=0.7)
    assert classifier.classify(mixed, _config()) == "mixed"


def test_origin_form_fillable():
    classifier = OriginClassifier()
    form = _summary(acroform_present=True)
    assert classifier.classify(form, _config()) == "form_fillable"

