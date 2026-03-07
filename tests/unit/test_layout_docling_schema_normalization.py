from src.models.document_profile import DocumentProfile, LanguageSignal
from src.strategies.base import ExtractionContext
from src.strategies.layout_aware import LayoutAwareExtractor


class _DoclingShapeProvider:
    name = "docling"

    def extract(self, file_path: str):
        return {
            "texts": [
                {
                    "text": "table heading",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {"l": 1, "t": 2, "r": 10, "b": 20},
                        }
                    ],
                }
            ],
            "tables": [
                {
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {"l": 0, "t": 0, "r": 100, "b": 100},
                        }
                    ],
                    "data": {
                        "table_cells": [
                            {"start_row_offset_idx": 0, "start_col_offset_idx": 0, "text": "h1"},
                            {"start_row_offset_idx": 0, "start_col_offset_idx": 1, "text": "h2"},
                            {"start_row_offset_idx": 1, "start_col_offset_idx": 0, "text": "a"},
                            {"start_row_offset_idx": 1, "start_col_offset_idx": 1, "text": "b"},
                        ]
                    },
                }
            ],
            "pictures": [],
            "pages": {"1": {"page_no": 1}},
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


def test_docling_shape_normalization(stage2_sample_pdf):
    extractor = LayoutAwareExtractor(provider=_DoclingShapeProvider())
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
    assert len(doc.text_blocks) == 1
    assert len(doc.tables) == 1
    assert doc.tables[0].headers == ["h1", "h2"]
    assert doc.tables[0].rows == [["a", "b"]]
