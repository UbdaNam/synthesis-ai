# Implementation Plan: PageIndex Builder

**Branch**: `004-page-index-builder` | **Date**: 2026-03-07 | **Spec**: [spec.md](C:\Abdu\synthesis-ai\specs\004-page-index-builder\spec.md)
**Input**: Feature specification from `/specs/004-page-index-builder/spec.md`

## Summary

Build Stage 4 as a LangGraph indexing stage that consumes validated Stage 3
`List[LDU]`, constructs a persisted hierarchical `PageIndex` tree, enriches each
section with deterministic entity and data-type signals, generates bounded GPT
section summaries, and prepares section-first retrieval through local Chroma
ingestion without expanding scope into final query-time answering.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**: Pydantic 2.11+, LangGraph 0.3+, LangChain OpenAI, OpenAI Python SDK, ChromaDB, PyYAML 6+, pytest 8+  
**Storage**: Filesystem JSON artifacts under `.refinery/pageindex/`, local Chroma persistence, and YAML configuration under `rubric/`  
**Testing**: pytest unit and integration suites  
**Target Platform**: Local and server-side Python runtime executing LangGraph pipelines  
**Project Type**: Single-project Python pipeline/library  
**Performance Goals**: Build a deterministic section tree in one indexing pass, keep summary requests bounded by configured chunk limits, and persist a complete PageIndex artifact for every successful Stage 4 run  
**Constraints**: Must consume validated Stage 3 LDUs directly from LangGraph state; must persist `.refinery/pageindex/{doc_id}.json`; must use OpenAI GPT for section summaries with structured bounded prompts; must use a real local vector database instead of mocks; runtime behavior must not depend on MCP; invalid index output must fail closed; scope is limited to Stage 4 only  
**Scale/Scope**: One new LangGraph indexing node, one new PageIndex model, modular indexing helpers under `src/indexing/`, Stage 4 configuration additions, persisted PageIndex artifacts, optional local vector ingestion, and focused unit/integration coverage for section-first retrieval preparation

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

- `Typed Contracts`: PASS. Stage 4 will accept only typed Stage 3 `LDU` inputs
  and emit explicit Pydantic `PageIndex` contracts plus typed state updates.
- `Determinism`: PASS. Section grouping, page-range computation, hierarchy
  construction, entity extraction defaults, and data-type detection remain
  deterministic; only section summarization uses an LLM with bounded inputs and
  explicit schema.
- `Architecture`: PASS. `src/agents/indexer.py` orchestrates, `src/indexing/`
  contains bounded transformation helpers, and `src/models/` defines contracts.
- `Provenance`: PASS. Every PageIndex node will remain traceable to source
  `chunk_ids`, section page ranges, and upstream content hashes through stored
  metadata.
- `Escalation Guard`: PASS. Invalid trees, unsupported summaries, or incomplete
  persistence fail closed and do not publish downstream-consumable state.
- `Performance/Cost`: PASS. OpenAI calls are limited to section summarization,
  bounded by configured chunk counts; vector ingestion is local and persisted.
- `Validation and Tests`: PASS. Design includes unit tests for hierarchy,
  summaries, entities, and vector preparation plus integration tests for
  end-to-end artifact emission.
- `Operability`: PASS. Stage 4 persists inspectable JSON artifacts, explicit
  index metadata, and a durable local vector collection for section-first
  retrieval support.

## Project Structure

### Documentation (this feature)

```text
specs/004-page-index-builder/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- indexer-node-contract.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/
|-- agents/
|   |-- chunker.py
|   `-- indexer.py
|-- indexing/
|   |-- pageindex_builder.py
|   |-- section_summarizer.py
|   |-- entity_extractor.py
|   |-- data_type_detector.py
|   `-- vector_ingestor.py
|-- graph/
|   `-- graph.py
`-- models/
    |-- graph_state.py
    |-- ldu.py
    `-- page_index.py

rubric/
`-- extraction_rules.yaml

.refinery/
`-- pageindex/

tests/
|-- integration/
`-- unit/
```

**Structure Decision**: Extend the existing single-project LangGraph pipeline by
adding one new Stage 4 indexer node, one PageIndex model module, and focused
indexing helpers under `src/indexing/`. Stage 4 will consume the existing Stage
3 `LDU` contract from `GraphState`, persist JSON artifacts under `.refinery`,
and expose vector-ingestion and section-first narrowing support without adding a
parallel pipeline.

## Phase 0: Research

Research resolved all planning decisions without unresolved clarifications:

1. PageIndex contract shape and persistence format
2. Deterministic section-tree construction from Stage 3 LDUs
3. Rule-based entity extraction with optional LLM-free refinement boundaries
4. Stage 4 data-type detection strategy from chunk metadata
5. Bounded OpenAI summary generation with structured output expectations
6. Local vector database choice and ingestion metadata
7. LangGraph state integration for PageIndex outputs and retrieval candidates

## Phase 1: Design

### Data Model Approach

- Add `PageIndexNode` and document-level wrapper models in
  `src/models/page_index.py` as the canonical Stage 4 output.
- Extend `GraphState` with typed fields for page-index output, indexing errors,
  indexing metadata, and optional retrieval-preparation candidates.
- Reuse Stage 3 `LDU` as the only accepted upstream input contract.

### Indexing Architecture

- `src/agents/indexer.py`: public Stage 4 entrypoint; loads Stage 4 rules,
  consumes `state.chunked_document`, orchestrates tree building, entity
  extraction, data-type detection, summary generation, persistence, and optional
  vector ingestion.
- `src/indexing/pageindex_builder.py`: constructs ordered section hierarchy from
  `LDU.parent_section`, chunk ordering, and page coverage.
- `src/indexing/entity_extractor.py`: deterministic rule-based entity extraction
  with configurable normalization and optional bounded refinement hooks.
- `src/indexing/data_type_detector.py`: derives `tables`, `figures`,
  `equations`, `narrative_text`, and `lists` from Stage 3 chunk types and
  metadata.
- `src/indexing/section_summarizer.py`: OpenAI-backed structured summary
  generator that only summarizes bounded source chunks from a single section.
- `src/indexing/vector_ingestor.py`: real ChromaDB persistence for LDU vectors
  and section metadata to support later section-first retrieval.

### LangGraph Integration

- Consume Stage 3 `List[LDU]` directly from `GraphState.chunked_document`.
- Add Stage 4 output fields such as `page_index`, `page_index_path`,
  `indexing_error`, `indexing_meta`, and `section_candidates`.
- Update `src/graph/graph.py` to insert `index` after `chunk`, yielding
  `triage -> extract -> chunk -> index`.

### Configuration Plan

Add a `pageindex` section in `rubric/extraction_rules.yaml` with:

- `rule_version`
- `summary_model_name`
- `max_chunks_per_summary_request`
- `summary_temperature`
- `vector_collection_name`
- `vector_persist_directory`
- `entity_extraction_stopwords`
- `entity_max_per_section`
- `section_ranking_strategy`
- `enable_vector_ingestion`

### Testing Plan

- Unit tests for section grouping, page-range correctness, nested-child
  relationships, data-type detection, deterministic entity formatting, summary
  schema/format validation, and vector-ingestion metadata mapping.
- Integration tests for `List[LDU] -> PageIndex JSON`, `List[LDU] -> Chroma
  ingestion`, and section-first narrowing helper behavior.

## Post-Design Constitution Check

- `Typed Contracts`: PASS. Design remains constrained to `LDU` inputs,
  `PageIndex` outputs, and typed state fields only.
- `Determinism`: PASS. Tree construction, section ranking, entity extraction,
  and data-type detection are deterministic; OpenAI is limited to bounded,
  schema-checked section summaries.
- `Architecture`: PASS. Orchestration, transformation, summarization, and model
  contracts remain modular.
- `Provenance`: PASS. Persisted PageIndex nodes will carry chunk references,
  page ranges, and traceability metadata.
- `Escalation Guard`: PASS. Summary/schema failures and invalid trees block
  downstream publication.
- `Performance/Cost`: PASS. Model usage is explicit, bounded per section, and
  isolated from vector ingestion and deterministic indexing logic.
- `Validation and Tests`: PASS. Design includes direct tests for hierarchy,
  summary structure, retrieval preparation, and failure paths.
- `Operability`: PASS. Stage 4 persists JSON artifacts and vector collections
  locally for inspection and later retrieval use.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| None      | N/A        | N/A                                  |
