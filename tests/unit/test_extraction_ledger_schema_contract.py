import json
from pathlib import Path

import jsonschema

from src.models.extracted_document import ExtractionLedgerEntry


def test_ledger_schema_contract():
    schema = json.loads(
        Path("specs/002-multi-strategy-extraction-engine/contracts/extraction-ledger-entry.schema.json").read_text(encoding="utf-8-sig")
    )
    payload = ExtractionLedgerEntry(
        doc_id="doc-1",
        strategy_used="fast_text",
        confidence_score=0.8,
        cost_estimate=0.01,
        processing_time=0.1,
        escalation_flag=False,
        threshold_rule_reference="extraction-v1",
    ).model_dump(mode="json")
    jsonschema.validate(instance=payload, schema=schema)
