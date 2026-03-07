# Tasks: Semantic Chunking Engine

**Input**: Design documents from `/specs/003-semantic-chunking-engine/`
**Prerequisites**: [plan.md](C:\Abdu\synthesis-ai\specs\003-semantic-chunking-engine\plan.md), [spec.md](C:\Abdu\synthesis-ai\specs\003-semantic-chunking-engine\spec.md), [research.md](C:\Abdu\synthesis-ai\specs\003-semantic-chunking-engine\research.md), [data-model.md](C:\Abdu\synthesis-ai\specs\003-semantic-chunking-engine\data-model.md), [chunker-node-contract.md](C:\Abdu\synthesis-ai\specs\003-semantic-chunking-engine\contracts\chunker-node-contract.md)

**Tests**: Unit and integration tests are mandatory for this governed Stage 3 pipeline change.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Stage 3 scaffolding and configuration surfaces for chunking work.

- [ ] T001 Create Stage 3 module scaffolding in `src/agents/chunker.py`, `src/models/ldu.py`, `src/models/chunk_relationship.py`, `src/chunking/engine.py`, `src/chunking/validator.py`, `src/chunking/reference_resolver.py`, `src/chunking/token_counter.py`, and `src/chunking/hash_generator.py`
- [ ] T002 [P] Add Stage 3 configuration placeholders under `chunking` in `rubric/extraction_rules.yaml`
- [ ] T003 [P] Create Stage 3 test skeletons in `tests/unit/test_ldu_schema.py`, `tests/unit/test_chunk_relationship_schema.py`, and `tests/integration/test_chunker_end_to_end.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the shared contracts, state integration, deterministic helpers, and validation surfaces required before any user story work begins.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Define the `LDU` Pydantic schema in `src/models/ldu.py`
- [ ] T005 Define the `ChunkRelationship` Pydantic schema in `src/models/chunk_relationship.py`
- [ ] T006 Extend `GraphState` for Stage 3 outputs in `src/models/graph_state.py`
- [ ] T007 [P] Implement deterministic token counting in `src/chunking/token_counter.py`
- [ ] T008 [P] Implement stable LDU content hash generation in `src/chunking/hash_generator.py`
- [ ] T009 [P] Implement cross-reference detection and resolution primitives in `src/chunking/reference_resolver.py`
- [ ] T010 Implement `ChunkValidator` invariants and failure categories in `src/chunking/validator.py`
- [ ] T011 Externalize Stage 3 thresholds and rule settings in `rubric/extraction_rules.yaml`
- [ ] T012 Add foundational schema and helper tests in `tests/unit/test_ldu_schema.py`, `tests/unit/test_chunk_relationship_schema.py`, `tests/unit/test_token_counter.py`, and `tests/unit/test_hash_generator.py`

**Checkpoint**: Stage 3 typed contracts, deterministic helpers, and validator foundation are ready for story implementation.

---

## Phase 3: User Story 1 - Produce Retrieval-Ready LDUs (Priority: P1) MVP

**Goal**: Convert the existing Stage 2 `ExtractedDocument` from LangGraph state into schema-valid retrieval-ready LDUs.

**Independent Test**: Run Stage 3 against a mixed `ExtractedDocument` fixture and verify that the chunker emits only valid LDUs with required fields and deterministic metadata.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add unit test for Stage 3 entrypoint state handling in `tests/unit/test_chunker_agent.py`
- [ ] T014 [P] [US1] Add unit test for text chunk construction from `ExtractedDocument` in `tests/unit/test_chunking_text_blocks.py`
- [ ] T015 [P] [US1] Add unit test for heading and section metadata propagation in `tests/unit/test_section_propagation.py`
- [ ] T016 [P] [US1] Add integration test for `ExtractedDocument -> ChunkingEngine -> validated List[LDU]` in `tests/integration/test_chunker_end_to_end.py`

### Implementation for User Story 1

- [ ] T017 [US1] Implement `ChunkingEngine` reading-order traversal over the existing `ExtractedDocument` schema in `src/chunking/engine.py`
- [ ] T018 [US1] Implement heading and section context tracking in `src/chunking/engine.py`
- [ ] T019 [US1] Implement text chunk construction in `src/chunking/engine.py`
- [ ] T020 [US1] Implement the Semantic Chunking Engine entrypoint in `src/agents/chunker.py`
- [ ] T021 [US1] Wire Stage 3 node state emission through `GraphState` in `src/agents/chunker.py` and `src/models/graph_state.py`
- [ ] T022 [US1] Integrate Stage 3 into the LangGraph flow in `src/graph/graph.py`

**Checkpoint**: Stage 3 consumes the existing Stage 2 `ExtractedDocument` contract directly and emits schema-valid LDUs for mixed narrative content.

---

## Phase 4: User Story 2 - Preserve Structural Meaning (Priority: P2)

**Goal**: Preserve section, table, figure, list, and cross-reference structure so chunking remains faithful to document semantics.

**Independent Test**: Process a mixed-content `ExtractedDocument` containing headings, tables, figures, numbered lists, and cross-references, then verify the five required chunking rules hold in emitted LDUs and relationships.

### Tests for User Story 2

- [ ] T023 [P] [US2] Add unit test for structured table chunking with repeated headers in `tests/unit/test_table_chunking.py`
- [ ] T024 [P] [US2] Add unit test for figure chunk caption metadata attachment in `tests/unit/test_figure_chunking.py`
- [ ] T025 [P] [US2] Add unit test for numbered list grouping and controlled splitting in `tests/unit/test_numbered_list_chunking.py`
- [ ] T026 [P] [US2] Add unit test for cross-reference detection and resolution in `tests/unit/test_reference_resolution.py`
- [ ] T027 [P] [US2] Add integration test for mixed-content structural preservation in `tests/integration/test_chunker_mixed_content.py`

### Implementation for User Story 2

- [ ] T028 [US2] Implement structured table chunk construction with header preservation in `src/chunking/engine.py`
- [ ] T029 [US2] Implement figure chunk construction with caption metadata in `src/chunking/engine.py`
- [ ] T030 [US2] Implement numbered list grouping and controlled splitting in `src/chunking/engine.py`
- [ ] T031 [US2] Implement cross-reference resolution and relationship attachment in `src/chunking/engine.py` and `src/chunking/reference_resolver.py`
- [ ] T032 [US2] Implement `belongs_to_section` and `follows` relationship emission in `src/chunking/engine.py`

**Checkpoint**: Tables preserve header context, figures preserve caption metadata, numbered lists remain intact unless splitting is necessary, section metadata propagates correctly, and cross-references are stored as relationships.

---

## Phase 5: User Story 3 - Fail Safely and Audit Runs (Priority: P3)

**Goal**: Explicitly enforce the five chunking rules and fail closed when output is invalid, while producing auditable Stage 3 run metadata.

**Independent Test**: Run valid and invalid Stage 3 fixtures and verify that valid runs pass validator enforcement while invalid runs fail closed with structured chunking errors and audit metadata.

### Tests for User Story 3

- [ ] T033 [P] [US3] Add unit tests for the five chunking-rule validations in `tests/unit/test_chunk_validator_rules.py`
- [ ] T034 [P] [US3] Add unit tests for validator failure cases in `tests/unit/test_chunk_validator_failures.py`
- [ ] T035 [P] [US3] Add integration test for fail-closed chunking behavior in `tests/integration/test_chunker_fail_closed.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement explicit enforcement of all five chunking rules in `src/chunking/validator.py`
- [ ] T037 [US3] Implement required-field, relationship-consistency, and provenance validation in `src/chunking/validator.py`
- [ ] T038 [US3] Add chunking audit metadata and structured error emission in `src/agents/chunker.py`
- [ ] T039 [US3] Add persisted Stage 3 audit settings and rule-version usage in `rubric/extraction_rules.yaml` and `src/agents/chunker.py`

**Checkpoint**: All five challenge chunking rules are explicitly enforced through `ChunkValidator`, and invalid Stage 3 outputs fail closed with auditability preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize Stage 3 readiness, remove drift, and validate documented scenarios.

- [ ] T040 [P] Document Stage 3 chunking configuration and output expectations in `README.md`
- [ ] T041 Reconcile Stage 3 quickstart scenarios with final implementation expectations in `specs/003-semantic-chunking-engine/quickstart.md`
- [ ] T042 Run and stabilize the full Stage 3 test suite in `tests/unit/` and `tests/integration/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because structural chunking builds on the core engine and entrypoint.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because validator enforcement must inspect the final structural outputs.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on later stories; this is the MVP scope.
- **User Story 2 (P2)**: Extends the Stage 3 engine with structural preservation rules.
- **User Story 3 (P3)**: Hardens the completed Stage 3 flow with fail-closed validation and auditing.

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Core models and deterministic helpers come before orchestration.
- Engine behavior comes before integration wiring.
- Validation and auditing come after chunk construction behavior is in place.

### Parallel Opportunities

- `T002` and `T003` can run in parallel after `T001`.
- `T007`, `T008`, and `T009` can run in parallel after `T004` and `T005`.
- `T013` through `T016` can run in parallel within User Story 1.
- `T023` through `T027` can run in parallel within User Story 2.
- `T033` through `T035` can run in parallel within User Story 3.

---

## Parallel Example: User Story 2

```bash
Task: "Add unit test for structured table chunking with repeated headers in tests/unit/test_table_chunking.py"
Task: "Add unit test for figure chunk caption metadata attachment in tests/unit/test_figure_chunking.py"
Task: "Add unit test for numbered list grouping and controlled splitting in tests/unit/test_numbered_list_chunking.py"
Task: "Add unit test for cross-reference detection and resolution in tests/unit/test_reference_resolution.py"
Task: "Add integration test for mixed-content structural preservation in tests/integration/test_chunker_mixed_content.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational contracts and deterministic helpers.
3. Complete Phase 3: User Story 1.
4. Validate Stage 3 direct consumption of `ExtractedDocument` and schema-valid `LDU` emission.

### Incremental Delivery

1. Deliver Stage 3 MVP with valid LDU emission from Stage 2 normalized output.
2. Add structural preservation for tables, figures, numbered lists, sections, and references.
3. Add fail-closed validation and auditability hardening.
4. Finish with documentation and full-suite stabilization.

## Notes

- All tasks are scoped to Stage 3 only.
- No task includes page index building, vector ingestion, fact extraction, or query-agent work.
- Acceptance for this task list requires direct Stage 2 `ExtractedDocument` consumption, explicit `ChunkValidator` enforcement of all five challenge rules, deterministic token counting and hash generation, and schema-valid `LDU` output.
