from src.models.document_profile import DocumentProfile, LanguageSignal
from src.strategies.fast_text import FastTextExtractor
from src.strategies.base import ExtractionContext


def _profile() -> DocumentProfile:
    return DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )


def test_fast_text_confidence_signal_scoring(stage2_sample_pdf, temp_config):
    extractor = FastTextExtractor()
    context = ExtractionContext(
        doc_id="doc-1",
        file_path=str(stage2_sample_pdf),
        document_profile=_profile(),
        rules={
            "extraction": {
                "fast_text": {
                    "confidence_signals": {
                        "char_count_min": 20,
                        "char_density_min": 0.0001,
                        "image_ratio_max": 0.95,
                        "font_metadata_required": False,
                    },
                    "weights": {
                        "char_count": 0.35,
                        "char_density": 0.35,
                        "image_to_page_ratio": 0.2,
                        "font_metadata_presence": 0.1,
                    },
                }
            }
        },
    )
    result = extractor.extract(context)
    assert result.confidence_score >= 0.0
    assert result.confidence_score <= 1.0
    assert result.document is not None
