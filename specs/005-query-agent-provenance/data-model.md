# Data Model: Query Agent and Provenance Layer

## QueryRequest

- Purpose: Represents a user-issued question or claim against one processed document.
- Fields:
  - `doc_id`: target processed document identifier
  - `user_query`: natural-language question or claim text
  - `mode`: `question_answering` or `audit`
  - `preferred_retrieval_path`: optional hint derived from deterministic routing
  - `section_filters`: optional narrowed PageIndex section identifiers
- Validation rules:
  - `doc_id` and `user_query` are required
  - `mode` must be one of the supported stage modes

## ProvenanceChainItem

- Purpose: Canonical source citation attached to answer evidence.
- Fields:
  - `document_name`
  - `page_number`
  - `bounding_box`
  - `content_hash`
  - `chunk_id`: optional source chunk identifier
  - `section_id`: optional PageIndex section identifier
  - `fact_id`: optional FactTable row identifier
- Validation rules:
  - `document_name`, `page_number`, `bounding_box`, and `content_hash` are required for supported evidence
  - at least one of `chunk_id` or `fact_id` should be present for internal traceability

## QueryResult

- Purpose: Typed final answer emitted by the Query Agent.
- Fields:
  - `answer`
  - `provenance_chain`
  - `support_status`: `supported`, `not_found`, or `unverifiable`
  - `retrieval_path_used`: ordered list of tool names used during the run
  - `matched_section_ids`: optional narrowed section identifiers
  - `matched_fact_ids`: optional SQLite fact identifiers
  - `metadata`: stage diagnostics and audit flags
- Validation rules:
  - supported answers require a non-empty provenance chain
  - `not_found` and `unverifiable` may omit provenance but must include explanatory metadata
  - `retrieval_path_used` values must come from the three supported tools

## PageIndexNavigationResult

- Purpose: Normalized output of `pageindex_navigate`.
- Fields:
  - `doc_id`
  - `query`
  - `matched_sections`: list of section summaries with IDs, titles, page ranges, scores, and optional child section IDs
- Validation rules:
  - scores are deterministic numeric values
  - returned sections must exist in the persisted PageIndex artifact

## SemanticSearchHit

- Purpose: Normalized semantic retrieval hit over retrieval-ready LDUs.
- Fields:
  - `chunk_id`
  - `doc_id`
  - `section_id`
  - `content`
  - `score`
  - `page_refs`
  - `bounding_box`
  - `content_hash`
  - `chunk_type`
- Validation rules:
  - provenance fields must be present on every hit
  - `section_id` is optional only when section metadata is genuinely unavailable

## FactRecord

- Purpose: SQLite-backed structured fact row for financial and numerical lookup.
- Fields:
  - `fact_id`
  - `doc_id`
  - `fact_name`
  - `fact_value`
  - `value_type`
  - `unit`: optional currency, percentage, or measurement unit
  - `period`: optional fiscal or reporting period
  - `source_chunk_id`
  - `document_name`
  - `page_number`
  - `bounding_box`
  - `content_hash`
  - `section_id`: optional PageIndex section linkage
- Validation rules:
  - exact source linkage is mandatory
  - `fact_name` and `fact_value` are required
  - numeric facts preserve original textual value for auditability even if parsed into normalized numeric columns

## AuditResult

- Purpose: Specialized result for claim verification.
- Fields:
  - `claim`
  - `support_status`: `supported`, `not_found`, or `unverifiable`
  - `explanation`
  - `provenance_chain`
  - `retrieval_path_used`
- Validation rules:
  - `supported` requires provenance
  - `not_found` and `unverifiable` require a non-empty explanation

## QueryGraphState additions

- Purpose: Extend the existing shared graph state with Stage 5 query fields.
- Fields:
  - `query_request`
  - `query_result`
  - `query_messages`
  - `navigation_candidates`
  - `semantic_hits`
  - `structured_rows`
  - `query_error`
  - `query_meta`
- State transitions:
  - Start with a validated `QueryRequest`
  - Tool nodes populate intermediate retrieval fields
  - Finalize node emits `QueryResult` or a fail-closed `query_error`
