import json

from src.models.document_profile import DocumentProfile, LanguageSignal


def test_profile_serialization_is_stable():
    profile = DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.9),
        domain_hint="technical",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    payload = profile.model_dump(mode="json")
    encoded_1 = json.dumps(payload, sort_keys=True)
    encoded_2 = json.dumps(payload, sort_keys=True)
    assert encoded_1 == encoded_2

