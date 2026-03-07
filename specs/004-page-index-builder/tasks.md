# Tasks: PageIndex Builder

**Input**: Design documents from `/specs/004-page-index-builder/`
**Prerequisites**: [plan.md](C:\Abdu\synthesis-ai\specs\004-page-index-builder\plan.md), [spec.md](C:\Abdu\synthesis-ai\specs\004-page-index-builder\spec.md), [research.md](C:\Abdu\synthesis-ai\specs\004-page-index-builder\research.md), [data-model.md](C:\Abdu\synthesis-ai\specs\004-page-index-builder\data-model.md), [indexer-node-contract.md](C:\Abdu\synthesis-ai\specs\004-page-index-builder\contracts\indexer-node-contract.md)

**Tests**: Unit and integration tests are mandatory for this governed Stage 4 pipeline change.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Stage 4 scaffolding, dependencies, and configuration surfaces for PageIndex work.

- [ ] T001 Create Stage 4 module scaffolding in `src/agents/indexer.py`, `src/models/page_index.py`, `src/indexing/pageindex_builder.py`, `src/indexing/section_summarizer.py`, `src/indexing/entity_extractor.py`, `src/indexing/data_type_detector.py`, and `src/indexing/vector_ingestor.py`
- [ ] T002 [P] Add Stage 4 dependencies for OpenAI summary generation and ChromaDB ingestion in `pyproject.toml`
- [ ] T003 [P] Add Stage 4 environment variable examples for OpenAI and local vector persistence in `.env.example`
- [ ] T004 [P] Add Stage 4 configuration placeholders under `pageindex` in `rubric/extraction_rules.yaml`
- [ ] T005 [P] Create Stage 4 test skeletons in `tests/unit/test_page_index_schema.py`, `tests/unit/test_pageindex_builder.py`, `tests/unit/test_section_summarizer.py`, and `tests/integration/test_pageindex_end_to_end.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the shared contracts, state integration, deterministic helpers, and persistence boundaries required before any user story work begins.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Define the `PageIndexNode`, `PageIndexDocument`, `SectionSummaryRequest`, `SectionSummaryResult`, and `SectionCandidate` Pydantic schemas in `src/models/page_index.py`
- [ ] T007 Extend Stage 4 graph state fields for `page_index`, `page_index_path`, `indexing_meta`, `section_candidates`, and `indexing_error` in `src/models/graph_state.py`
- [ ] T008 [P] Implement deterministic section and node identifier generation in `src/indexing/pageindex_builder.py`
- [ ] T009 [P] Implement PageIndex JSON persistence helpers targeting `.refinery/pageindex/{doc_id}.json` in `src/indexing/pageindex_builder.py`
- [ ] T010 [P] Implement deterministic data type normalization primitives for `tables`, `figures`, `equations`, `narrative_text`, and `lists` in `src/indexing/data_type_detector.py`
- [ ] T011 [P] Implement deterministic rule-based entity normalization primitives in `src/indexing/entity_extractor.py`
- [ ] T012 Configure Stage 4 thresholds and settings including summary model, chunk limits, vector collection, and ranking strategy in `rubric/extraction_rules.yaml`
- [ ] T013 Add foundational schema and helper tests in `tests/unit/test_page_index_schema.py`, `tests/unit/test_pageindex_builder.py`, and `tests/unit/test_data_type_detector.py`

**Checkpoint**: Stage 4 typed contracts, persistence, deterministic helpers, and graph-state foundation are ready for story implementation.

---

## Phase 3: User Story 1 - Build Navigable Section Hierarchy (Priority: P1) MVP

**Goal**: Convert validated Stage 3 LDUs into a persisted hierarchical PageIndex that downstream retrieval can navigate by section.

**Independent Test**: Submit validated Stage 3 LDUs representing a multi-section document and verify that Stage 4 emits a persisted PageIndex tree whose nodes contain titles, page ranges, and child section relationships.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add unit test for section grouping and tree construction in `tests/unit/test_pageindex_builder.py`
- [ ] T015 [P] [US1] Add unit test for page range correctness and child section relationships in `tests/unit/test_pageindex_ranges.py`
- [ ] T016 [P] [US1] Add unit test for indexer state input/output handling in `tests/unit/test_indexer_agent.py`
- [ ] T017 [P] [US1] Add integration test for `List[LDU] -> PageIndex JSON` in `tests/integration/test_pageindex_end_to_end.py`

### Implementation for User Story 1

- [ ] T018 [US1] Implement deterministic section grouping and hierarchy construction from Stage 3 LDUs in `src/indexing/pageindex_builder.py`
- [ ] T019 [US1] Implement page range derivation, section titles, and child section assembly in `src/indexing/pageindex_builder.py`
- [ ] T020 [US1] Implement PageIndex artifact persistence under `.refinery/pageindex/` in `src/indexing/pageindex_builder.py`
- [ ] T021 [US1] Implement the Stage 4 indexer entrypoint to consume real Stage 3 LDUs from graph state in `src/agents/indexer.py`
- [ ] T022 [US1] Wire Stage 4 state emission through `src/agents/indexer.py` and `src/models/graph_state.py`
- [ ] T023 [US1] Integrate the `index` node into the LangGraph flow in `src/graph/graph.py`

**Checkpoint**: Stage 4 consumes real Stage 3 LDUs directly and persists schema-valid PageIndex artifacts with hierarchical section navigation.

---

## Phase 4: User Story 2 - Summarize and Characterize Sections (Priority: P2)

**Goal**: Enrich each PageIndex section with deterministic entities and data types plus a bounded OpenAI GPT summary grounded in that section’s LDUs only.

**Independent Test**: Process validated Stage 3 LDUs containing mixed content and verify that every PageIndex node includes a correctly structured summary, deterministic key entities, and accurate `data_types_present`.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add unit test for deterministic entity extraction formatting in `tests/unit/test_entity_extractor.py`
- [ ] T025 [P] [US2] Add unit test for section data type detection in `tests/unit/test_data_type_detector.py`
- [ ] T026 [P] [US2] Add unit test for OpenAI summary request shaping and structured output validation in `tests/unit/test_section_summarizer.py`
- [ ] T027 [P] [US2] Add integration test for mixed-content section enrichment in `tests/integration/test_pageindex_section_enrichment.py`

### Implementation for User Story 2

- [ ] T028 [US2] Implement rule-based key entity extraction for section LDUs in `src/indexing/entity_extractor.py`
- [ ] T029 [US2] Implement `data_types_present` detection from Stage 3 chunk types and metadata in `src/indexing/data_type_detector.py`
- [ ] T030 [US2] Implement bounded summary request assembly for one section at a time in `src/indexing/section_summarizer.py`
- [ ] T031 [US2] Implement real LangChain OpenAI GPT summary generation with structured output validation in `src/indexing/section_summarizer.py`
- [ ] T032 [US2] Integrate section enrichment orchestration into `src/agents/indexer.py`
- [ ] T033 [US2] Add summary generation safeguards that fail closed on invalid or ungrounded output in `src/indexing/section_summarizer.py` and `src/agents/indexer.py`

**Checkpoint**: PageIndex nodes include all required fields, summaries are generated with LangGraph-compatible OpenAI GPT usage, and section enrichment remains grounded and deterministic where practical.

---

## Phase 5: User Story 3 - Support Section-First Retrieval Safely (Priority: P3)

**Goal**: Persist a usable retrieval-preparation layer with real vector ingestion, deterministic section ranking, and fail-closed boundaries that keep Stage 4 isolated from final query-agent behavior.

**Independent Test**: Run Stage 4 on valid and structurally incomplete Stage 3 outputs and verify that valid runs persist the PageIndex and local vector collection while invalid runs fail without publishing misleading navigation or retrieval candidates.

### Tests for User Story 3

- [ ] T034 [P] [US3] Add unit test for vector ingestion metadata mapping in `tests/unit/test_vector_ingestor.py`
- [ ] T035 [P] [US3] Add unit test for section-first narrowing and ranking behavior in `tests/unit/test_section_candidate_ranking.py`
- [ ] T036 [P] [US3] Add unit test for Stage 4 fail-closed validation and error categories in `tests/unit/test_indexer_fail_closed.py`
- [ ] T037 [P] [US3] Add integration test for `List[LDU] -> vector ingestion` in `tests/integration/test_pageindex_vector_ingestion.py`
- [ ] T038 [P] [US3] Add integration test for section-first narrowing preparation in `tests/integration/test_pageindex_section_narrowing.py`

### Implementation for User Story 3

- [ ] T039 [US3] Implement real ChromaDB ingestion for LDUs with required metadata in `src/indexing/vector_ingestor.py`
- [ ] T040 [US3] Implement section-first narrowing and deterministic ranking helper in `src/agents/indexer.py`
- [ ] T041 [US3] Implement Stage 4 validation and fail-closed publishing checks for invalid trees, summaries, and mixed-document inputs in `src/agents/indexer.py` and `src/indexing/pageindex_builder.py`
- [ ] T042 [US3] Enforce Stage 4 isolation from final query-agent behavior in `src/agents/indexer.py` and `src/graph/graph.py`
- [ ] T043 [US3] Emit indexing metadata for persisted artifacts, vector ingestion status, and retrieval candidates in `src/agents/indexer.py`

**Checkpoint**: Vector ingestion is real, not mocked; PageIndex artifacts are persisted correctly; section-first narrowing works for downstream retrieval preparation; and Stage 4 remains isolated from final query-agent behavior.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize Stage 4 readiness, documentation, and end-to-end validation.

- [ ] T044 [P] Document Stage 4 configuration, OpenAI requirements, persisted artifacts, and retrieval-preparation outputs in `README.md`
- [ ] T045 Reconcile Stage 4 quickstart scenarios with final implementation behavior in `specs/004-page-index-builder/quickstart.md`
- [ ] T046 [P] Add regression coverage for PageIndex artifact persistence and state contract boundaries in `tests/integration/test_pageindex_persistence_regression.py`
- [ ] T047 Run and stabilize the full Stage 4 test suite in `tests/unit/` and `tests/integration/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because section enrichment attaches to the constructed PageIndex tree.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because vector ingestion and narrowing rely on persisted enriched sections.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on later stories; this is the MVP scope.
- **User Story 2 (P2)**: Extends the persisted hierarchy with summaries, entities, and data-type descriptors.
- **User Story 3 (P3)**: Hardens Stage 4 with real vector ingestion, retrieval preparation, and fail-closed boundaries.

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Models and state contracts come before orchestration.
- Tree construction comes before section enrichment.
- Section enrichment comes before vector ingestion and retrieval preparation.
- Fail-closed validation must be completed before publishing artifacts downstream.

### Parallel Opportunities

- `T002`, `T003`, `T004`, and `T005` can run in parallel after `T001`.
- `T008`, `T009`, `T010`, and `T011` can run in parallel after `T006` and `T007`.
- `T014` through `T017` can run in parallel within User Story 1.
- `T024` through `T027` can run in parallel within User Story 2.
- `T034` through `T038` can run in parallel within User Story 3.

---

## Parallel Example: User Story 2

```bash
Task: "Add unit test for deterministic entity extraction formatting in tests/unit/test_entity_extractor.py"
Task: "Add unit test for section data type detection in tests/unit/test_data_type_detector.py"
Task: "Add unit test for OpenAI summary request shaping and structured output validation in tests/unit/test_section_summarizer.py"
Task: "Add integration test for mixed-content section enrichment in tests/integration/test_pageindex_section_enrichment.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational contracts, state integration, and persistence helpers.
3. Complete Phase 3: User Story 1.
4. Validate direct Stage 3 `LDU` consumption and persisted PageIndex tree emission.

### Incremental Delivery

1. Deliver Stage 4 MVP with real `List[LDU] -> PageIndex JSON` output.
2. Add deterministic section enrichment plus bounded OpenAI summaries.
3. Add real Chroma ingestion and section-first narrowing support.
4. Finish with documentation, regression coverage, and suite stabilization.

## Notes

- All tasks are scoped to Stage 4 only.
- No task includes final query-agent behavior, audit mode behavior, or final answer generation.
- Acceptance for this task list requires real Stage 3 `LDU` consumption, complete PageIndex node fields, LangGraph-compatible OpenAI GPT summaries, real vector ingestion, persisted PageIndex artifacts, section-first narrowing, and strict Stage 4 isolation.
