# Data Model: Stage 2 Structure Extraction Layer

## 1. ExtractedDocument

Purpose: normalized output from all strategies.

Fields:
- `doc_id` (str)
- `strategy_used` (`fast_text | layout_aware | vision`)
- `confidence_score` (0..1)
- `metadata` (includes `page_count`, provider/model metadata, and optional `handwriting_detected`)
- `text_blocks[]`, `tables[]`, `figures[]`

Validation:
- At least one content unit must exist.
- Every content unit must include `page_number`, `bounding_box`, `content_hash`.

## 2. VisionInvocationMetadata

Purpose: capture multimodal invocation and budget fields for Strategy C.

Fields:
- `provider` (e.g., `openrouter`)
- `model_name`
- `prompt_template_version`
- `handwriting_detected` (bool)
- `usage_tokens` (int)
- `estimated_cost` (float)

## 3. ExtractionAttemptRecord

Fields:
- `doc_id`
- `attempt_index`
- `strategy_used`
- `confidence_score`
- `cost_estimate`
- `usage_tokens` (int, optional for non-vision)
- `processing_time`
- `escalated`
- `rule_reference`

## 4. ExtractionLedgerEntry

Required minimum fields:
- `doc_id`
- `strategy_used`
- `confidence_score`
- `cost_estimate`
- `processing_time`
- `escalation_flag`
- `threshold_rule_reference`

Additional recommended:
- `usage_tokens`
- `budget_cap`
- `budget_spent`
- `final_disposition`
- `timestamp_utc`

## 5. GraphState Update

Add:
- `extracted_document: ExtractedDocument | None`
- `extraction_attempts: list[ExtractionAttemptRecord]`
- `extraction_error: str | None`

State transitions:
- `triaged -> extracting -> extracted`
- `triaged -> extracting -> failed_closed`
