# Query Agent Node Contract

## Purpose

Define the public Stage 5 LangGraph entrypoint contract for grounded question answering, structured fact retrieval, and audit-mode claim verification.

## Inputs

- `GraphState.doc_id`: required target document identifier
- `GraphState.page_index` or persisted `.refinery/pageindex/{doc_id}.json`: required navigation artifact
- `GraphState.chunked_document` or persisted Chroma collection metadata: required semantic retrieval source
- `QueryRequest`:
  - `doc_id`
  - `user_query`
  - `mode`
  - optional `preferred_retrieval_path`
  - optional `section_filters`

## Shared State Expectations

- Shared state must preserve intermediate retrieval results separately:
  - `navigation_candidates`
  - `semantic_hits`
  - `structured_rows`
- Shared state must preserve the ordered retrieval path used across tool invocations.
- Shared state must not contain raw tool-provider payloads after node boundaries.

## Tool Surface

The model must have exactly these three tools attached:

1. `pageindex_navigate`
2. `semantic_search`
3. `structured_query`

No additional user-visible or hidden retrieval tools may be attached to the model in this stage.

## Tool Input/Output Requirements

### `pageindex_navigate`
- Input:
  - `doc_id`
  - `topic`
  - optional `limit`
- Output:
  - ranked section candidates with section IDs, titles, page ranges, section summaries, scores, and child metadata

### `semantic_search`
- Input:
  - `doc_id`
  - `query`
  - optional `section_ids`
  - optional `limit`
- Output:
  - ranked LDU hits with `chunk_id`, `content`, `page_refs`, `bounding_box`, `content_hash`, `section_id`, and similarity score

### `structured_query`
- Input:
  - `doc_id`
  - `query`
  - optional `fact_filters`
  - optional `limit`
- Output:
  - structured fact rows with exact values plus provenance linkage fields

## Final Output Contract

The final node must emit a typed `QueryResult` containing:

- `answer`
- `provenance_chain`
- `support_status`
- `retrieval_path_used`

Additional diagnostics may be returned in `metadata`, but no supported result may omit provenance.

## Failure Semantics

- Missing PageIndex artifact: fail closed with a structured query error
- Missing Chroma collection or semantic hits: fail closed unless the answer is explicitly `not_found` or `unverifiable`
- Missing FactTable for a fact-heavy request: agent may fall back to other tools only if provenance remains sufficient
- Invalid final answer contract: fail closed and surface validation error
- Unsupported claim in audit mode: return `not_found` or `unverifiable`, never a fabricated supported result
