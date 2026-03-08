from src.models.document_profile import DocumentProfile, LanguageSignal
from src.strategies.layout_aware import LayoutAwareExtractor
from src.strategies.base import ExtractionContext


class _RichProvider:
    name = "docling"

    def extract(self, file_path: str):
        return {
            "page_count": 2,
            "text_blocks": [
                {
                    "id": "tb-1",
                    "text": "Heading",
                    "page_number": 1,
                    "reading_order": 0,
                    "block_type": "heading",
                    "bounding_box": {"x0": 1, "y0": 2, "x1": 10, "y1": 20},
                }
            ],
            "tables": [
                {
                    "id": "tbl-1",
                    "page_number": 1,
                    "headers": ["a", "b"],
                    "rows": [["1", "2"]],
                    "bounding_box": {"x0": 0, "y0": 0, "x1": 100, "y1": 100},
                }
            ],
            "figures": [
                {
                    "id": "fig-1",
                    "page_number": 2,
                    "caption": "Plot",
                    "figure_type": "chart",
                    "bounding_box": {"x0": 4, "y0": 5, "x1": 40, "y1": 50},
                }
            ],
        }


def _profile() -> DocumentProfile:
    return DocumentProfile(
        doc_id="doc-1",
        origin_type="mixed",
        layout_complexity="table_heavy",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="needs_layout_model",
        deterministic_version="triage-v1",
    )


def test_layout_provider_normalization(stage2_sample_pdf):
    extractor = LayoutAwareExtractor(provider=_RichProvider())
    result = extractor.extract(
        ExtractionContext(
            doc_id="doc-1",
            file_path=str(stage2_sample_pdf),
            document_profile=_profile(),
            rules={"extraction": {"costing": {"layout_base": 0.01, "layout_per_page": 0.001}}},
        )
    )
    assert result.document is not None
    doc = result.document
    assert doc.strategy_used == "layout_aware"
    assert doc.metadata["provider"] == "docling"
    assert len(doc.text_blocks) == 1
    assert len(doc.tables) == 1
    assert len(doc.figures) == 1
    assert doc.text_blocks[0].content_hash
    assert doc.tables[0].content_hash
    assert doc.figures[0].content_hash
