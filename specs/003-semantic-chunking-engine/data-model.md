# Data Model: Semantic Chunking Engine

## Entity: LDU

Purpose: Canonical Stage 3 logical document unit emitted for retrieval-ready
downstream use.

Fields:
- `id`: unique deterministic identifier for the chunk within a document
- `doc_id`: source document identifier
- `content`: canonical chunk text or serialized structural content
- `chunk_type`: logical category such as `section_text`, `numbered_list`,
  `table`, `figure`, `table_segment`, or `list_segment`
- `page_refs`: one or more source page references covered by the chunk
- `bounding_box`: normalized bounding box or aggregate source region reference
- `parent_section`: active section heading text or structured section reference
- `token_count`: deterministic token count for the chunk content
- `content_hash`: stable hash for provenance verification
- `relationships`: list of `ChunkRelationship` records linked from this chunk
- `metadata`: auxiliary structured metadata such as figure caption, repeated
  table headers, list continuity, upstream block ids, or source content hashes

Validation rules:
- All required fields must be present for every emitted LDU.
- `content_hash` must be deterministic for identical canonical content.
- `token_count` must be derived from the configured Stage 3 token counter only.
- `parent_section` must be populated for chunks under an active heading.
- `relationships` must contain only valid typed relationship records.

State transitions:
- `constructed` -> `validated` -> `emitted`
- `constructed` -> `rejected` when validation fails

## Entity: ChunkRelationship

Purpose: Typed link between LDUs or between an LDU and a structural target.

Fields:
- `id`: deterministic relationship identifier
- `doc_id`: source document identifier
- `source_chunk_id`: chunk where the relationship originates
- `target_chunk_id`: resolved target chunk when available
- `relationship_type`: one of `references_table`, `references_figure`,
  `references_section`, `belongs_to_section`, `follows`
- `target_label`: literal target label such as `Table 3` or `Section 4.1`
- `resolved`: whether the relationship was resolved to a known target
- `metadata`: additional context such as match text, sequence position, or
  section path

Validation rules:
- `relationship_type` must be from the approved enum.
- `source_chunk_id` is required.
- `target_chunk_id` is required when `resolved=true`.
- `target_label` is required for unresolved cross-references.

## Entity: ChunkingRunRecord

Purpose: Auditable record of a Stage 3 run.

Fields:
- `doc_id`
- `rule_version`
- `total_chunks_emitted`
- `total_relationships_emitted`
- `validation_status`
- `processing_time`
- `error_reason`
- `artifact_paths`

Validation rules:
- Failed runs must record `error_reason`.
- Successful runs must record chunk and relationship counts.

## Relationships

- One `ExtractedDocument` produces zero or more `LDU` records.
- One `LDU` may reference zero or more `ChunkRelationship` records.
- One `ChunkRelationship` links one source `LDU` to one target `LDU` or one
  unresolved structural label.
- One `ChunkingRunRecord` summarizes one Stage 3 execution for one `doc_id`.
