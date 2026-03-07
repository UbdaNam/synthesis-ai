from src.models.document_profile import DocumentProfile, LanguageSignal
from src.models.graph_state import GraphState
from tests.unit._stage2_test_utils import make_doc


def _profile(doc_id: str = "doc-1") -> DocumentProfile:
    return DocumentProfile(
        doc_id=doc_id,
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )


def test_graph_state_supports_extraction_transitions():
    state = GraphState(doc_id="doc-1", file_path="x.pdf", document_profile=_profile())
    assert state.extracted_document is None

    accepted = state.model_copy(update={"extracted_document": make_doc(), "extraction_error": None})
    assert accepted.extracted_document is not None
    assert accepted.extraction_error is None

    failed = state.model_copy(update={"extraction_error": "all_strategies_below_threshold"})
    assert failed.extracted_document is None
    assert failed.extraction_error == "all_strategies_below_threshold"
