# Extractor Node Contract

## Node

- Name: `extract`
- File: `C:/Abdu/synthesis-ai/src/agents/extractor.py`
- Graph wiring: added in `C:/Abdu/synthesis-ai/src/graph/graph.py` after `triage`

## Input Contract

Input type: `GraphState`

Required fields:
- `doc_id: str`
- `file_path: str`
- `document_profile: DocumentProfile` (must be present)

Optional fields:
- `extracted_document: ExtractedDocument | None` (must be `None` before node execution)

## Routing Rules

- Initial route by `document_profile.origin_type` and `document_profile.layout_complexity`.
- Deterministic rule execution only (no LLM-based router decisions).
- Escalation order is fixed: `fast_text -> layout_aware -> vision`.

## Output Contract

Output type: `GraphState`

Success output:
- `extracted_document` populated and schema-valid
- `extraction_error` empty/null
- attempt records available for tests/debug (if kept in state)

Fail-closed output:
- `extracted_document` unset/null
- `extraction_error` populated with explicit reason
- ledger contains final failed disposition and rule reference

## Ledger Requirement

For each attempt, append one JSON object to `.refinery/extraction_ledger.jsonl` with:
- `doc_id`
- `strategy_used`
- `confidence_score`
- `cost_estimate`
- `processing_time`
- `escalation_flag`
- `threshold_rule_reference`

## Determinism Requirement

Given same input document, identical `DocumentProfile`, identical strategy provider outputs, and identical YAML rules, strategy selection/escalation decisions must be identical across runs.
