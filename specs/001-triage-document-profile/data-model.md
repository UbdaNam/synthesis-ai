# Data Model: Stage 1 Triage Agent (Challenge Structure)

## 1. DocumentProfile

Purpose: Deterministic Stage 1 classification payload for downstream extraction strategy selection.

Fields:
- `doc_id` (string, required)
- `origin_type` (enum): `native_digital | scanned_image | mixed | form_fillable`
- `layout_complexity` (enum): `single_column | multi_column | table_heavy | figure_heavy | mixed`
- `language` (`LanguageSignal`, required)
- `domain_hint` (enum): `financial | legal | technical | medical | general`
- `estimated_extraction_cost` (enum): `fast_text_sufficient | needs_layout_model | needs_vision_model`
- `deterministic_version` (string)

Validation rules:
- Enum values must be from allowed sets.
- `language.confidence` must be in `[0.0, 1.0]`.
- Output must be deterministic for identical input + config.

## 2. GraphState

Purpose: LangGraph-compatible state for Stage 1 boundary (without Stage 2 expansion).

Fields:
- `doc_id` (string, required)
- `file_path` (string, required)
- `document_profile` (`DocumentProfile`, optional before triage, required after triage)

State transition:
- `initial` -> `profiled`

Runtime note:
- `GraphState` is the runtime I/O type for `src/graph/graph.py`.

## 3. LanguageSignal

Fields:
- `code` (string)
- `confidence` (float, `[0.0, 1.0]`)

## 4. ProfilingSignalSummary

Purpose: Captures deterministic classification inputs for explainability and audit.

Fields:
- `char_density` (array[number])
- `image_ratio` (array[number])
- `font_metadata_presence` (array[bool])
- `layout_signals` (object)

Validation rules:
- Array lengths must match analyzed page count.

## 5. ProfilingEvidenceEntry (Stage 1 triage event)

Purpose: Audit record written to `.refinery/profiling_ledger.jsonl`.

Fields:
- `doc_id`
- `char_density`
- `image_ratio`
- `font_metadata_presence`
- `layout_signals`
- `origin_type`
- `layout_complexity`
- `language`
- `domain_hint`
- `estimated_extraction_cost`
- `processing_time`
- `threshold_rule_reference`

Validation rules:
- `processing_time >= 0`
- All classification fields must be valid profile enum values.

