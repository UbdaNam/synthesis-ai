# Contract: Stage 4 Indexer Node

## Purpose

Define the typed LangGraph boundary for Stage 4 so indexing consumes validated
Stage 3 LDUs and emits a persisted PageIndex artifact plus indexing metadata.

## Input Contract

**Source**: `GraphState`

**Required fields**:

- `doc_id: str`
- `chunked_document: list[LDU]`

**Optional supporting fields**:

- `chunk_relationships: list[ChunkRelationship]`
- `chunking_meta: dict[str, Any]`

**Preconditions**:

- `chunked_document` must already be validated Stage 3 output.
- All LDUs must belong to the same `doc_id`.
- Every LDU must carry `page_refs`, `content_hash`, and `parent_section` or an
  explicit empty section marker.

## Output Contract

**Target**: `GraphState`

**Success fields**:

- `page_index: PageIndexDocument`
- `page_index_path: str`
- `indexing_meta: dict[str, Any]`
- `section_candidates: list[SectionCandidate]`
- `indexing_error: None`

**Failure fields**:

- `page_index: None`
- `page_index_path: None`
- `section_candidates: []`
- `indexing_error: str`
- `indexing_meta: dict[str, Any]`

## Success Guarantees

- `page_index_path` points to `.refinery/pageindex/{doc_id}.json`
- `page_index.section_count` matches the number of emitted nodes
- Every `PageIndexNode` contains:
  - `id`
  - `doc_id`
  - `title`
  - `page_start`
  - `page_end`
  - `child_sections`
  - `key_entities`
  - `summary`
  - `data_types_present`
- If vector ingestion is enabled, metadata stored with vectors includes:
  - `doc_id`
  - `section_id`
  - `section_title`
  - `page_refs`
  - `chunk_type`
  - `content_hash`

## Failure Modes

- `missing_chunked_document`
- `mixed_document_ids`
- `invalid_section_hierarchy`
- `summary_generation_failed`
- `pageindex_validation_failed`
- `pageindex_persistence_failed`
- `vector_ingestion_failed`

All failure modes are fail-closed: Stage 4 does not publish a downstream
PageIndex artifact on failure.
