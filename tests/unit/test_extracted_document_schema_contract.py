import json
from pathlib import Path

import jsonschema

from src.models.extracted_document import BoundingBox, ExtractedDocument, TextBlock


def test_extracted_document_matches_json_schema():
    schema_path = Path("specs/002-multi-strategy-extraction-engine/contracts/extracted-document.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
    payload = ExtractedDocument(
        doc_id="doc-1",
        strategy_used="fast_text",
        confidence_score=0.88,
        metadata={"page_count": 1},
        text_blocks=[
            TextBlock(
                id="tb1",
                page_number=1,
                bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                reading_order=0,
                block_type="paragraph",
                text="hello",
                content_hash="h1",
                confidence=0.8,
            )
        ],
        tables=[],
        figures=[],
    ).model_dump(mode="json")
    jsonschema.validate(instance=payload, schema=schema)
