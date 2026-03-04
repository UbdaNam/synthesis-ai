# Data Model: Stage 1 Triage Agent

## 1. GraphState

Purpose: Shared LangGraph state for Stage 1 entry and downstream handoff.

Fields:
- `doc_id` (string, required): Stable document identifier used for profile persistence path resolution.
- `file_path` (string, required): Absolute or repository-relative path to source PDF.
- `document_profile` (DocumentProfile, optional initially): Populated by triage node.

Relationships:
- One `GraphState` has zero or one `DocumentProfile` before triage.
- One `GraphState` has exactly one `DocumentProfile` after successful triage.

Validation rules:
- `doc_id` must be non-empty and filesystem-safe for profile filename.
- `file_path` must reference an existing readable PDF.

State transitions:
- `initial` -> `profiled` when triage completes and `document_profile` is assigned.

## 2. DocumentProfile

Purpose: Deterministic typed classification payload controlling extraction strategy routing.

Fields:
- `doc_id` (string, required)
- `origin_type` (enum, required): `native_digital | scanned_image | mixed | form_fillable`
- `layout_complexity` (enum, required): `single_column | multi_column | table_heavy | figure_heavy | mixed`
- `language` (LanguageSignal, required)
- `domain_hint` (enum, required): `financial | legal | technical | medical | general`
- `estimated_extraction_cost` (enum, required): `fast_text_sufficient | needs_layout_model | needs_vision_model`
- `analysis_summary` (AnalysisSummary, required)
- `created_at` (string datetime, required)
- `deterministic_version` (string, required): classifier ruleset/version identifier

Validation rules:
- All enum values must be in allowed sets.
- `analysis_summary.page_count` must be >= 1.
- `language.confidence` must be in `[0.0, 1.0]`.
- `doc_id` must match `GraphState.doc_id`.

## 3. LanguageSignal

Fields:
- `code` (string, required): BCP-47 or ISO language code
- `confidence` (number, required): range `[0.0, 1.0]`

Validation rules:
- `code` not empty.
- `confidence` within inclusive range.

## 4. AnalysisSummary

Purpose: Deterministic feature signals used for auditability and testing.

Fields:
- `page_count` (integer, required)
- `character_count_per_page` (array[int], required)
- `character_density` (array[number], required)
- `image_area_ratio` (array[number], required)
- `font_metadata_presence` (array[boolean], required)
- `bounding_box_distribution` (object, required): summarized geometric stats

Validation rules:
- Array lengths must equal `page_count`.
- Ratio values must be in `[0.0, 1.0]`.

## 5. DomainClassifierStrategy (interface contract)

Purpose: Pluggable strategy abstraction for `domain_hint`.

Input:
- Document text/features summary

Output:
- One enum value from `financial|legal|technical|medical|general`

Validation rules:
- Strategy must always return an allowed value.
- Strategy must be deterministic for identical inputs/configuration.
