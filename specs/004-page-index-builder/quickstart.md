# Quickstart: PageIndex Builder

## Goal

Validate Stage 4 by running the LangGraph pipeline from Stage 3 chunk outputs to
a persisted PageIndex artifact and real local Chroma ingestion.

## Preconditions

- Stage 3 has already produced validated `List[LDU]` for a document.
- `OPENAI_API_KEY` is configured for summary generation and embeddings.
- Local Stage 4 configuration exists in `rubric/extraction_rules.yaml`.

## Scenario 1: Build and persist a PageIndex tree

1. Load or generate a `GraphState` containing:
   - `doc_id`
   - `chunked_document`
2. Invoke the Stage 4 indexer node.
3. Verify the resulting state contains:
   - `page_index`
   - `page_index_path`
   - `indexing_meta`
4. Confirm the persisted artifact exists at:
   - `.refinery/pageindex/{doc_id}.json`
5. Inspect the JSON and verify:
   - root sections exist
   - nested `child_sections` are preserved
   - every node has `title`, `page_start`, `page_end`, `key_entities`,
     `summary`, and `data_types_present`

## Scenario 2: Mixed-content section enrichment

1. Prepare Stage 3 LDUs containing:
   - narrative text
   - tables
   - figures
   - lists
2. Run Stage 4.
3. Verify each section node reports the correct `data_types_present`.
4. Confirm key entities are deterministic across repeated runs with the same
   input and configuration.
5. Confirm section summaries stay bounded to the supplied section content.

## Scenario 3: Section-first narrowing support

1. Persist a successful PageIndex artifact and vector collection.
2. Invoke the retrieval-preparation helper with a topic string.
3. Confirm the helper ranks the most relevant sections before any full-corpus
   semantic search step.
4. Confirm the returned candidates reference valid section IDs and page ranges.
5. Confirm vector metadata includes `doc_id`, `section_id`, `section_title`,
   `page_refs`, `chunk_type`, and `content_hash`.

## Scenario 4: Fail-closed behavior

1. Provide malformed Stage 3 inputs such as:
   - empty `chunked_document`
   - mixed `doc_id` values
   - invalid page ranges
2. Run Stage 4.
3. Confirm:
   - no persisted JSON artifact is published as a successful output
   - `indexing_error` is populated
   - failure metadata is retained for inspection
