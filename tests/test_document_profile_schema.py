import json

from jsonschema import validate

from src.models.document_profile import DocumentProfile, LanguageSignal


def test_document_profile_json_schema_validation():
    profile = DocumentProfile(
        doc_id="doc-1",
        origin_type="native_digital",
        layout_complexity="single_column",
        language=LanguageSignal(code="en", confidence=0.99),
        domain_hint="general",
        estimated_extraction_cost="fast_text_sufficient",
        deterministic_version="triage-v1",
    )
    schema = DocumentProfile.model_json_schema()
    validate(instance=json.loads(profile.model_dump_json()), schema=schema)

