# Triage Node Interface Contract (Stage 1 Only)

## Purpose

Define the Stage 1 triage contract centered on `GraphState -> GraphState` with deterministic document profiling.

## Graph Module Boundary

- `src/graph/graph.py` owns LangGraph assembly and compilation.
- `src/agents/triage.py` owns callable triage logic used by the graph node.
- `main.py` invokes compiled graph via `build_graph(...)`.

## Input Contract

- Input type: `GraphState`
- Required fields:
  - `doc_id`: string
  - `file_path`: string (PDF path)
- Optional field before execution:
  - `document_profile`: null/absent

## Output Contract

- Output type: `GraphState`
- Guarantees:
  - `document_profile` exists and is schema-valid after successful triage
  - `doc_id` and `file_path` are preserved

## Required Triage Signals

- character density
- embedded image ratio
- font metadata presence
- layout signals (column/table/figure heuristics)

## Required Final Profile Fields

- `origin_type`
- `layout_complexity`
- `language` (code + confidence)
- `domain_hint`
- `estimated_extraction_cost`

## Deterministic Behavior Contract

- Same input file + same rule config => identical classification fields and cost class.
- Language detection must return deterministic code/confidence under fixed configuration.
- No LLM-based origin/layout decisioning.

## Persistence Contract

- Persist profile JSON at `.refinery/profiles/{doc_id}.json`.
- Persist Stage 1 profiling evidence events at `.refinery/profiling_ledger.jsonl`.

Each Stage 1 profiling entry MUST include:
- `doc_id`
- computed metrics (`char_density`, `image_ratio`, layout signals)
- final `origin_type`
- final `layout_complexity`
- final `language`
- final `estimated_extraction_cost`
- `processing_time`

## Error Contract

- Missing/unreadable input PDF: fail with explicit typed error.
- Invalid output schema: fail closed and do not emit partial downstream state.

## Stage Boundary

This contract covers only Stage 1 triage and profiling. Extraction content artifacts are intentionally deferred to Stage 2.

