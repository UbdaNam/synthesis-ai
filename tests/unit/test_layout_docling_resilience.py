from src.models.document_profile import DocumentProfile, LanguageSignal
from src.strategies.base import ExtractionContext
from src.strategies.layout_aware import DoclingLayoutProvider, LayoutAwareExtractor


def _profile(origin_type: str = "native_digital") -> DocumentProfile:
    return DocumentProfile(
        doc_id="doc-1",
        origin_type=origin_type,  # type: ignore[arg-type]
        layout_complexity="table_heavy",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="needs_layout_model",
        deterministic_version="triage-v1",
    )


class _RetryableDoclingProvider(DoclingLayoutProvider):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def extract(self, file_path: str, force_ocr: bool = False):  # type: ignore[override]
        self.calls += 1
        if not force_ocr:
            return {
                "_provider_meta": {"provider": "docling", "status": "success", "do_ocr": False},
                "texts": [],
                "tables": [],
                "pictures": [],
                "pages": {"1": {"page_no": 1}},
            }
        return {
            "_provider_meta": {"provider": "docling", "status": "success", "do_ocr": True},
            "texts": [
                {
                    "text": "Recovered with OCR",
                    "prov": [{"page_no": 1, "bbox": {"l": 1, "t": 2, "r": 10, "b": 20}}],
                }
            ],
            "tables": [],
            "pictures": [],
            "pages": {"1": {"page_no": 1}},
        }


class _FailingProvider:
    name = "docling"

    def extract(self, file_path: str):
        raise RuntimeError("docling_conversion_failed:failure:test")


def test_docling_empty_payload_retries_with_ocr(stage2_sample_pdf):
    provider = _RetryableDoclingProvider()
    extractor = LayoutAwareExtractor(provider=provider)
    result = extractor.extract(
        ExtractionContext(
            doc_id="doc-1",
            file_path=str(stage2_sample_pdf),
            document_profile=_profile("mixed"),
            rules={"extraction": {"costing": {"layout_base": 0.01, "layout_per_page": 0.001}}},
        )
    )
    assert result.error is None
    assert result.document is not None
    assert provider.calls == 2
    assert result.document.metadata["provider_ocr_enabled"] is True


def test_layout_provider_error_is_classified(stage2_sample_pdf):
    extractor = LayoutAwareExtractor(provider=_FailingProvider())
    result = extractor.extract(
        ExtractionContext(
            doc_id="doc-1",
            file_path=str(stage2_sample_pdf),
            document_profile=_profile(),
            rules={"extraction": {"costing": {"layout_base": 0.01, "layout_per_page": 0.001}}},
        )
    )
    assert result.document is None
    assert result.error is not None
    assert result.error.startswith("layout_provider_conversion_failed:")
