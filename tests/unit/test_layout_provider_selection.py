from src.models.document_profile import DocumentProfile, LanguageSignal
from src.strategies.layout_aware import LayoutAwareExtractor
from src.strategies.base import ExtractionContext


class _Provider:
    def __init__(self, name: str):
        self.name = name

    def extract(self, file_path: str):
        return {
            "page_count": 1,
            "text_blocks": [
                {
                    "text": "hello",
                    "page_number": 1,
                    "bounding_box": {"x0": 0, "y0": 0, "x1": 10, "y1": 10},
                }
            ],
            "tables": [],
            "figures": [],
        }


def _profile() -> DocumentProfile:
    return DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="table_heavy",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="needs_layout_model",
        deterministic_version="triage-v1",
    )


def test_layout_provider_selection_from_rules(stage2_sample_pdf):
    extractor = LayoutAwareExtractor()
    rules_docling = {"extraction": {"layout_aware": {"provider": "docling"}}}
    rules_mineru = {"extraction": {"layout_aware": {"provider": "mineru"}}}
    assert extractor._provider_from_rules(rules_docling).name == "docling"
    assert extractor._provider_from_rules(rules_mineru).name == "mineru"


def test_layout_provider_selection_injected_provider(stage2_sample_pdf):
    provider = _Provider("docling")
    extractor = LayoutAwareExtractor(provider=provider)
    result = extractor.extract(
        ExtractionContext(
            doc_id="doc-1",
            file_path=str(stage2_sample_pdf),
            document_profile=_profile(),
            rules={"extraction": {"costing": {"layout_base": 0.01, "layout_per_page": 0.001}}},
        )
    )
    assert result.document is not None
    assert result.document.metadata["provider"] == "docling"
