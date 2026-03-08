# Data Model: PageIndex Builder

## PageIndexDocument

**Purpose**: Document-level Stage 4 artifact persisted to JSON and handed to
downstream retrieval preparation.

**Fields**:

- `doc_id: str`
- `root_sections: list[PageIndexNode]`
- `section_count: int`
- `chunk_count: int`
- `artifact_path: str`
- `rule_version: str`
- `generated_at: datetime`
- `metadata: dict[str, Any]`

**Relationships**:

- Owns zero or more root `PageIndexNode` records.
- References the Stage 3 chunk corpus through aggregated `chunk_count` and per
  node `chunk_ids`.

**Validation rules**:

- `doc_id` must match the Stage 3 document identifier.
- `root_sections` must contain only nodes without `parent_section_id`.
- `section_count` must equal the total number of nodes in the tree.
- `artifact_path` must resolve to `.refinery/pageindex/{doc_id}.json`.

## PageIndexNode

**Purpose**: Canonical section node for the navigable PageIndex hierarchy.

**Fields**:

- `id: str`
- `doc_id: str`
- `title: str`
- `page_start: int`
- `page_end: int`
- `child_sections: list[PageIndexNode]`
- `key_entities: list[str]`
- `summary: str`
- `data_types_present: list[str]`
- `parent_section_id: str | None`
- `chunk_ids: list[str] | None`
- `metadata: dict[str, Any]`

**Relationships**:

- May reference one parent `PageIndexNode`.
- May own zero or more child `PageIndexNode` values.
- Maps to one or more Stage 3 `LDU` records through `chunk_ids`.

**Validation rules**:

- `title` must be non-empty after normalization.
- `page_start` must be less than or equal to `page_end`.
- `child_sections` must contain only nodes whose `parent_section_id` matches
  the current node `id`.
- `data_types_present` must be unique normalized values from the configured
  supported set.
- `summary` must be present for successful persisted output.

## SectionSummaryRequest

**Purpose**: Bounded input contract for section summarization.

**Fields**:

- `doc_id: str`
- `section_id: str`
- `section_title: str`
- `chunk_ids: list[str]`
- `source_chunks: list[str]`

**Validation rules**:

- `source_chunks` must be capped by the configured maximum chunks per request.
- All chunk content must belong to the same section.

## SectionSummaryResult

**Purpose**: Structured output returned by the summarizer before insertion into a
`PageIndexNode`.

**Fields**:

- `section_id: str`
- `summary: str`
- `source_chunk_ids: list[str]`

**Validation rules**:

- `summary` must be 2-3 sentences in the validated format expected by tests.
- `source_chunk_ids` must be a subset of the request chunk IDs.

## SectionCandidate

**Purpose**: Lightweight retrieval-preparation record for section-first
narrowing.

**Fields**:

- `section_id: str`
- `title: str`
- `score: float`
- `page_start: int`
- `page_end: int`
- `matched_terms: list[str]`

**Validation rules**:

- `score` must be deterministic for the same topic string and identical inputs.
- Candidates must reference an existing `PageIndexNode`.

## State Transitions

1. Stage 3 provides validated `List[LDU]` in graph state.
2. Stage 4 groups LDUs into hierarchical section candidates.
3. Section candidates are enriched with entities, data types, and summaries.
4. Fully validated nodes are assembled into `PageIndexDocument`.
5. `PageIndexDocument` is persisted to `.refinery/pageindex/{doc_id}.json`.
6. Optional vector ingestion stores the LDU corpus plus section metadata for
   later retrieval preparation.
