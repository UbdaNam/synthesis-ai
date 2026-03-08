# Contract: Stage 3 Chunker Node

## Purpose

Define the typed input, output, and failure contract for the public Stage 3
entrypoint implemented in `src/agents/chunker.py`.

## Input Contract

Source: `GraphState`

Required input fields:
- `doc_id: str`
- `extracted_document: ExtractedDocument`

Optional supporting input fields:
- `extraction_meta: dict[str, Any]`

Preconditions:
- `extracted_document` must be present.
- `extracted_document` must already satisfy Stage 2 normalization rules.
- Stage 3 must not accept raw provider payloads or untyped chunk seeds.

## Output Contract

Stage 3 updates `GraphState` with:
- `chunked_document: list[LDU]`
- `chunking_error: str | None`
- `chunking_meta: dict[str, Any]`

Expected success behavior:
- `chunked_document` contains only validated `LDU` records.
- `chunking_error` is `None`.
- `chunking_meta` includes rule version, chunk count, relationship count, and
  audit artifact references.

Expected failure behavior:
- `chunked_document` is empty or omitted according to the final typed state
  model.
- `chunking_error` contains a structured fail-closed error category.
- No partial unvalidated LDU list is published as downstream-ready output.

## Relationship Contract

Each `LDU.relationships` entry must use the `ChunkRelationship` schema and
support at minimum:
- `references_table`
- `references_figure`
- `references_section`
- `belongs_to_section`
- `follows`

## Validation Guarantees

`src/chunking/validator.py` must reject outputs that violate any of the
following:
- required field completeness
- table header preservation
- figure caption attachment
- numbered list integrity
- section metadata inheritance
- relationship consistency

## Out of Scope

This contract explicitly excludes:
- page index construction
- vector store ingestion
- fact table extraction
- query agent behavior
