# Tasks: Triage Agent Document Profiling

**Input**: Design documents from `/specs/001-triage-document-profile/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included because the spec explicitly requires unit tests and deterministic behavior validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label for story-phase tasks only (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an absolute file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize project structure and dependencies for Stage 1 implementation.

- [ ] T001 Create package directories for triage stage in `C:\Abdu\synthesis-ai\src\synthesis_ai\models\`, `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\`, and `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\`
- [ ] T002 [P] Create test directories for Stage 1 in `C:\Abdu\synthesis-ai\tests\unit\` and `C:\Abdu\synthesis-ai\tests\fixtures\pdf_samples\`
- [ ] T003 Update dependencies in `C:\Abdu\synthesis-ai\pyproject.toml` to include `pydantic`, `langgraph`, and `pytest`
- [ ] T004 Create package init files in `C:\Abdu\synthesis-ai\src\synthesis_ai\__init__.py`, `C:\Abdu\synthesis-ai\src\synthesis_ai\models\__init__.py`, `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\__init__.py`, and `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core typed contracts and reusable primitives required by all user stories.

**CRITICAL**: No user story work starts before this phase is complete.

- [ ] T005 Implement `DocumentProfile` enums and models in `C:\Abdu\synthesis-ai\src\synthesis_ai\models\document_profile.py`
- [ ] T006 Implement `GraphState` model with optional `document_profile` in `C:\Abdu\synthesis-ai\src\synthesis_ai\models\graph_state.py`
- [ ] T007 Implement profile persistence utility for `.refinery/profiles/{doc_id}.json` in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profile_repository.py`
- [ ] T008 [P] Implement deterministic extraction-cost mapping contract in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\extraction_cost_resolver.py`
- [ ] T009 [P] Create shared triage configuration constants (thresholds, deterministic version) in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\config.py`

**Checkpoint**: Foundation ready for independent user story implementation.

---

## Phase 3: User Story 1 - Route Extraction by Document Type (Priority: P1) MVP

**Goal**: Classify PDF origin and layout deterministically and route extraction cost.

**Independent Test**: Run triage on representative native/scanned/mixed/form-fillable PDFs and verify `origin_type`, `layout_complexity`, and `estimated_extraction_cost` are correctly set.

### Tests for User Story 1

- [ ] T010 [P] [US1] Add origin classification unit tests in `C:\Abdu\synthesis-ai\tests\unit\test_origin_classifier.py`
- [ ] T011 [P] [US1] Add layout classification unit tests in `C:\Abdu\synthesis-ai\tests\unit\test_layout_classifier.py`
- [ ] T012 [P] [US1] Add extraction cost resolver unit tests in `C:\Abdu\synthesis-ai\tests\unit\test_extraction_cost_resolver.py`
- [ ] T013 [P] [US1] Add PDF stats analyzer unit tests for character density/image ratio/font metadata/bbox distributions in `C:\Abdu\synthesis-ai\tests\unit\test_pdf_stats_analyzer.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `PDFStatsAnalyzer` using `pdfplumber` in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\pdf_stats_analyzer.py`
- [ ] T015 [US1] Implement `OriginClassifier` with native/scanned/mixed/form_fillable logic in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\origin_classifier.py`
- [ ] T016 [US1] Implement `LayoutClassifier` with x-clustering/grid-alignment/figure-heavy heuristics in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\layout_classifier.py`
- [ ] T017 [US1] Finalize deterministic mapping logic for origin+layout to cost in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\extraction_cost_resolver.py`
- [ ] T018 [US1] Implement Stage 1 `TriageNode` as first LangGraph node in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_pipeline.py`
- [ ] T019 [US1] Wire analyzer/classifiers/cost resolver into triage pipeline orchestration in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_pipeline.py`

**Checkpoint**: US1 independently classifies and routes documents correctly.

---

## Phase 4: User Story 2 - Preserve Deterministic Typed Output (Priority: P2)

**Goal**: Guarantee schema-valid, persisted, deterministic `DocumentProfile` output.

**Independent Test**: Execute triage twice for the same input and confirm persisted JSON equality and schema-valid structure.

### Tests for User Story 2

- [ ] T020 [P] [US2] Add profile persistence tests for `.refinery/profiles/{doc_id}.json` in `C:\Abdu\synthesis-ai\tests\unit\test_profile_repository.py`
- [ ] T021 [P] [US2] Add deterministic rerun equality tests in `C:\Abdu\synthesis-ai\tests\unit\test_determinism.py`
- [ ] T022 [P] [US2] Add JSON schema compliance tests against contract schema in `C:\Abdu\synthesis-ai\tests\unit\test_document_profile_schema.py`
- [ ] T023 [P] [US2] Add graph-state contract tests for typed first-node output in `C:\Abdu\synthesis-ai\tests\unit\test_triage_pipeline_contract.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement idempotent profile JSON persistence and overwrite semantics in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profile_repository.py`
- [ ] T025 [US2] Implement deterministic serialization helpers (stable field ordering/encoding) in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\serialization.py`
- [ ] T026 [US2] Integrate persistence into triage node completion path in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_pipeline.py`
- [ ] T027 [US2] Add schema validator utility for `DocumentProfile` contract in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\schema_validation.py`

**Checkpoint**: US2 independently guarantees deterministic typed persisted output.

---

## Phase 5: User Story 3 - Support Domain-Aware Routing Policies (Priority: P3)

**Goal**: Provide pluggable domain classification with a default keyword strategy.

**Independent Test**: Run triage on domain-focused samples and verify domain hints are valid and strategy-swappable without changing output contract.

### Tests for User Story 3

- [ ] T028 [P] [US3] Add domain strategy interface behavior tests in `C:\Abdu\synthesis-ai\tests\unit\test_domain_strategy.py`
- [ ] T029 [P] [US3] Add keyword-domain classifier scoring tests in `C:\Abdu\synthesis-ai\tests\unit\test_keyword_domain_classifier.py`
- [ ] T030 [P] [US3] Add pipeline domain integration tests with strategy injection in `C:\Abdu\synthesis-ai\tests\unit\test_domain_integration.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `DomainClassifierStrategy` interface in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\domain\strategy.py`
- [ ] T032 [US3] Implement keyword-frequency domain classifier in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\domain\keyword_strategy.py`
- [ ] T033 [US3] Integrate pluggable domain strategy into triage node assembly in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_pipeline.py`

**Checkpoint**: US3 independently delivers pluggable domain hint classification.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final alignment, validation, and developer ergonomics across stories.

- [ ] T034 [P] Add end-to-end Stage 1 smoke test covering all profile dimensions in `C:\Abdu\synthesis-ai\tests\unit\test_triage_end_to_end.py`
- [ ] T035 [P] Update entrypoint wiring/examples for Stage 1 execution in `C:\Abdu\synthesis-ai\main.py` and `C:\Abdu\synthesis-ai\README.md`
- [ ] T036 Run and fix full test suite for Stage 1 in `C:\Abdu\synthesis-ai\tests\`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; recommended MVP.
- **Phase 4 (US2)**: Depends on Phase 2 and US1 pipeline baseline.
- **Phase 5 (US3)**: Depends on Phase 2 and US1 pipeline baseline.
- **Phase 6 (Polish)**: Depends on completion of selected user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on other stories.
- **US2 (P2)**: Starts after US1 pipeline exists; focuses on determinism/persistence.
- **US3 (P3)**: Starts after US1 pipeline exists; domain strategy work is independent of US2.

### Dependency Graph

`Setup -> Foundational -> US1 -> (US2 || US3) -> Polish`

---

## Parallel Execution Opportunities

- **Setup**: `T002` and `T004` can run in parallel after `T001`.
- **Foundational**: `T008` and `T009` can run in parallel after `T005/T006/T007` scaffolding decisions.
- **US1**: `T010`, `T011`, `T012`, `T013` can run in parallel; then `T014`, `T015`, `T016` can run in parallel before `T018/T019`.
- **US2**: `T020`, `T021`, `T022`, `T023` can run in parallel; `T024`, `T025`, `T027` can run in parallel before `T026`.
- **US3**: `T028`, `T029`, `T030` can run in parallel; `T031` and `T032` can run in parallel before `T033`.

## Parallel Example: User Story 1

```text
Task: "T010 [US1] Add origin classification unit tests in C:\Abdu\synthesis-ai\tests\unit\test_origin_classifier.py"
Task: "T011 [US1] Add layout classification unit tests in C:\Abdu\synthesis-ai\tests\unit\test_layout_classifier.py"
Task: "T012 [US1] Add extraction cost resolver unit tests in C:\Abdu\synthesis-ai\tests\unit\test_extraction_cost_resolver.py"
Task: "T013 [US1] Add PDF stats analyzer unit tests in C:\Abdu\synthesis-ai\tests\unit\test_pdf_stats_analyzer.py"
```

## Parallel Example: User Story 2

```text
Task: "T020 [US2] Add profile persistence tests in C:\Abdu\synthesis-ai\tests\unit\test_profile_repository.py"
Task: "T021 [US2] Add deterministic rerun equality tests in C:\Abdu\synthesis-ai\tests\unit\test_determinism.py"
Task: "T022 [US2] Add schema compliance tests in C:\Abdu\synthesis-ai\tests\unit\test_document_profile_schema.py"
Task: "T023 [US2] Add graph-state contract tests in C:\Abdu\synthesis-ai\tests\unit\test_triage_pipeline_contract.py"
```

## Parallel Example: User Story 3

```text
Task: "T028 [US3] Add domain strategy interface tests in C:\Abdu\synthesis-ai\tests\unit\test_domain_strategy.py"
Task: "T029 [US3] Add keyword-domain classifier tests in C:\Abdu\synthesis-ai\tests\unit\test_keyword_domain_classifier.py"
Task: "T030 [US3] Add domain integration tests in C:\Abdu\synthesis-ai\tests\unit\test_domain_integration.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independent test criteria with known documents.
4. Stop for MVP review.

### Incremental Delivery

1. Add US2 for deterministic persistence and schema compliance.
2. Add US3 for pluggable domain hinting.
3. Execute Phase 6 polish and final full-suite validation.

### Suggested MVP Scope

- **Recommended MVP**: US1 only (origin/layout/cost routing as first LangGraph node).

