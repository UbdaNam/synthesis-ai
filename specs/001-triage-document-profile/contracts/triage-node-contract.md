# Triage Node Interface Contract

## Purpose

Define the Stage 1 contract between graph orchestration and document triage classification.

## Input Contract

- Input type: `GraphState`
- Required fields:
  - `doc_id`: string
  - `file_path`: string (PDF path)
- Optional fields:
  - `document_profile`: null or absent before triage execution

## Output Contract

- Output type: `GraphState`
- Guarantees:
  - `document_profile` is present and schema-valid after successful triage
  - `doc_id` and `file_path` are preserved

## Behavioral Guarantees

- Deterministic for identical input file and configuration
- No LLM-based origin/layout decisions
- Cost routing is fail-closed (ambiguous/low confidence routes to higher-cost class)

## Persistence Contract

- Persist profile to `.refinery/profiles/{doc_id}.json`
- Persistence must be idempotent for reruns with same `doc_id`

## Error Contract

- Invalid/missing PDF path: return explicit failure event (no partial profile)
- Unreadable PDF content: fail with typed error and no downstream routing
- Schema validation failure: fail-closed and log classification diagnostics
