# Tasks: Stage 1 Triage Agent & Document Profiling

**Input**: Design documents from `/specs/001-triage-document-profile/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are explicitly required by the specification (determinism, known samples, schema validation, graph entrypoint contract).

**Organization**: Tasks are grouped by user story and constrained to Stage 1 only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label for story-phase tasks only (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Stage 1 layout, dependencies, and configuration.

- [ ] T001 Create Stage 1 directories in `C:\Abdu\synthesis-ai\src\models\`, `C:\Abdu\synthesis-ai\src\agents\`, `C:\Abdu\synthesis-ai\src\graph\`, `C:\Abdu\synthesis-ai\rubric\`, `C:\Abdu\synthesis-ai\.refinery\profiles\`, and `C:\Abdu\synthesis-ai\tests\`
- [ ] T002 [P] Add Stage 1 runtime dependencies (`pydantic`, `pdfplumber`, `langdetect`, `langgraph`, `pytest`) in `C:\Abdu\synthesis-ai\pyproject.toml`
- [ ] T003 [P] Create package bootstrap modules in `C:\Abdu\synthesis-ai\src\models\__init__.py`, `C:\Abdu\synthesis-ai\src\agents\__init__.py`, and `C:\Abdu\synthesis-ai\src\graph\__init__.py`
- [ ] T004 Define deterministic thresholds/rules in `C:\Abdu\synthesis-ai\rubric\extraction_rules.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build typed contracts and shared utilities required by all stories.

**CRITICAL**: No user story work starts before this phase is complete.

- [ ] T005 Implement `DocumentProfile` Pydantic schema in `C:\Abdu\synthesis-ai\src\models\document_profile.py`
- [ ] T006 Implement `GraphState` Pydantic schema in `C:\Abdu\synthesis-ai\src\models\graph_state.py`
- [ ] T007 Implement triage configuration loader and deterministic controls in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T008 [P] Implement deterministic extraction cost resolver in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T009 [P] Implement profile persistence utility to `.refinery/profiles/{doc_id}.json` in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T010 [P] Implement profiling evidence writer to `.refinery/profiling_ledger.jsonl` in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T011 Implement graph assembly function `build_graph(...)` in `C:\Abdu\synthesis-ai\src\graph\graph.py`

**Checkpoint**: Foundation ready for independent user story implementation.

---

## Phase 3: User Story 1 - Route Extraction by Document Type (Priority: P1) MVP

**Goal**: Analyze PDF signals and classify origin/layout/cost with graph-first execution.

**Independent Test**: Run graph on known native_digital, scanned_image, mixed, and form_fillable samples and verify classification outputs.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add PDF statistics analysis tests in `C:\Abdu\synthesis-ai\tests\test_pdf_statistics.py`
- [ ] T013 [P] [US1] Add origin type detection tests (`native_digital|scanned_image|mixed|form_fillable`) in `C:\Abdu\synthesis-ai\tests\test_origin_detection.py`
- [ ] T014 [P] [US1] Add layout complexity detection tests in `C:\Abdu\synthesis-ai\tests\test_layout_detection.py`
- [ ] T015 [P] [US1] Add extraction cost mapping tests in `C:\Abdu\synthesis-ai\tests\test_extraction_cost_estimation.py`
- [ ] T016 [P] [US1] Add graph entrypoint contract tests for `build_graph` and `GraphState` I/O in `C:\Abdu\synthesis-ai\tests\test_graph_entrypoint_contract.py`
- [ ] T017 [P] [US1] Add SC-004 rule tests for advanced-processing set in `C:\Abdu\synthesis-ai\tests\test_sc004_advanced_processing_rule.py`

### Implementation for User Story 1

- [ ] T018 [US1] Implement PDF signal analysis in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T019 [US1] Implement origin type detection in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T020 [US1] Implement layout complexity detection in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T021 [US1] Implement triage node callable for graph execution in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T022 [US1] Wire graph entrypoint/finish to `triage` in `C:\Abdu\synthesis-ai\src\graph\graph.py`
- [ ] T023 [US1] Implement graph-first runtime path in `C:\Abdu\synthesis-ai\main.py`

**Checkpoint**: US1 independently classifies and routes documents through graph execution.

---

## Phase 4: User Story 2 - Preserve Deterministic Typed Output (Priority: P2)

**Goal**: Persist schema-valid deterministic profiles and reproducible decision evidence.

**Independent Test**: Repeated runs with same input/config produce identical profile payload and matching decision evidence.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add deterministic repeat-run test for profile payload in `C:\Abdu\synthesis-ai\tests\test_deterministic_repeatability.py`
- [ ] T025 [P] [US2] Add `DocumentProfile` JSON schema validation test in `C:\Abdu\synthesis-ai\tests\test_document_profile_schema.py`
- [ ] T026 [P] [US2] Add deterministic serialization consistency test in `C:\Abdu\synthesis-ai\tests\test_profile_serialization.py`
- [ ] T027 [P] [US2] Add profile persistence idempotency/path tests in `C:\Abdu\synthesis-ai\tests\test_profile_persistence.py`
- [ ] T028 [P] [US2] Add required evidence-fields completeness test in `C:\Abdu\synthesis-ai\tests\test_decision_evidence_fields.py`
- [ ] T029 [P] [US2] Add repeat-run evidence determinism test in `C:\Abdu\synthesis-ai\tests\test_decision_evidence_repeatability.py`
- [ ] T030 [P] [US2] Add profiling ledger JSONL format test in `C:\Abdu\synthesis-ai\tests\test_profiling_ledger_format.py`

### Implementation for User Story 2

- [ ] T031 [US2] Implement deterministic profile serialization in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T032 [US2] Implement idempotent profile overwrite behavior in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T033 [US2] Implement required decision-evidence payload generation in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T034 [US2] Implement profiling ledger output contract in `C:\Abdu\synthesis-ai\src\agents\triage.py`

**Checkpoint**: US2 independently guarantees deterministic typed profile + evidence output.

---

## Phase 5: User Story 3 - Support Domain-Aware & Language Detection (Priority: P3)

**Goal**: Support pluggable domain classification and deterministic language detection.

**Independent Test**: Domain and language fields are deterministic and valid on repeated runs.

### Tests for User Story 3

- [ ] T035 [P] [US3] Add pluggable domain classifier interface tests in `C:\Abdu\synthesis-ai\tests\test_domain_classifier_interface.py`
- [ ] T036 [P] [US3] Add keyword domain classifier behavior tests in `C:\Abdu\synthesis-ai\tests\test_keyword_domain_classifier.py`
- [ ] T037 [P] [US3] Add deterministic language detection tests (English + non-English + confidence) in `C:\Abdu\synthesis-ai\tests\test_language_detection.py`

### Implementation for User Story 3

- [ ] T038 [US3] Implement pluggable domain strategy and default keyword classifier in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T039 [US3] Implement deterministic `langdetect` integration (`DetectorFactory.seed = 0`) in `C:\Abdu\synthesis-ai\src\agents\triage.py`
- [ ] T040 [US3] Integrate domain/language fields into final `DocumentProfile` in `C:\Abdu\synthesis-ai\src\agents\triage.py`

**Checkpoint**: US3 independently delivers domain and language requirements.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Validate Stage 1 graph runtime and final quality bar.

- [ ] T041 [P] Add known-sample validation suite in `C:\Abdu\synthesis-ai\tests\test_known_sample_validation.py`
- [ ] T042 [P] Add Stage 1 graph smoke test in `C:\Abdu\synthesis-ai\tests\test_triage_smoke.py`
- [ ] T043 [P] Add main entrypoint graph-runner test in `C:\Abdu\synthesis-ai\tests\test_main_entrypoint.py`
- [ ] T044 [P] Update run/use documentation in `C:\Abdu\synthesis-ai\specs\001-triage-document-profile\quickstart.md`
- [ ] T045 Run and stabilize full Stage 1 test suite in `C:\Abdu\synthesis-ai\tests\`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; recommended MVP.
- **Phase 4 (US2)**: Depends on US1 baseline pipeline.
- **Phase 5 (US3)**: Depends on US1 baseline pipeline.
- **Phase 6 (Polish)**: Depends on US1 + US2 + US3 completion.

### User Story Dependencies

- **US1 (P1)**: Starts after foundational phase.
- **US2 (P2)**: Depends on US1 graph execution and persistence behavior.
- **US3 (P3)**: Depends on US1 graph execution and extends classification fields.

### Dependency Graph

`Setup -> Foundational -> US1 -> (US2 || US3) -> Polish`

---

## Parallel Execution Opportunities

- **Setup**: `T002`, `T003` can run in parallel.
- **Foundational**: `T008`, `T009`, `T010` can run in parallel after schemas.
- **US1**: `T012-T017` can run in parallel; `T018-T021` can run in parallel before `T022` and `T023`.
- **US2**: `T024-T030` can run in parallel; `T031-T034` run sequentially by integration dependency.
- **US3**: `T035-T037` can run in parallel; `T038` and `T039` can run in parallel before `T040`.
- **Polish**: `T041-T044` can run in parallel before `T045`.

## Parallel Example: User Story 1

```text
Task: "T012 [US1] Add PDF statistics analysis tests in C:\Abdu\synthesis-ai\tests\test_pdf_statistics.py"
Task: "T013 [US1] Add origin detection tests in C:\Abdu\synthesis-ai\tests\test_origin_detection.py"
Task: "T014 [US1] Add layout detection tests in C:\Abdu\synthesis-ai\tests\test_layout_detection.py"
Task: "T016 [US1] Add graph entrypoint contract tests in C:\Abdu\synthesis-ai\tests\test_graph_entrypoint_contract.py"
```

## Parallel Example: User Story 2

```text
Task: "T024 [US2] Add deterministic repeatability test in C:\Abdu\synthesis-ai\tests\test_deterministic_repeatability.py"
Task: "T025 [US2] Add profile schema test in C:\Abdu\synthesis-ai\tests\test_document_profile_schema.py"
Task: "T028 [US2] Add evidence field completeness test in C:\Abdu\synthesis-ai\tests\test_decision_evidence_fields.py"
Task: "T030 [US2] Add profiling ledger format test in C:\Abdu\synthesis-ai\tests\test_profiling_ledger_format.py"
```

## Parallel Example: User Story 3

```text
Task: "T035 [US3] Add domain strategy interface tests in C:\Abdu\synthesis-ai\tests\test_domain_classifier_interface.py"
Task: "T036 [US3] Add keyword domain classifier tests in C:\Abdu\synthesis-ai\tests\test_keyword_domain_classifier.py"
Task: "T037 [US3] Add language detection tests in C:\Abdu\synthesis-ai\tests\test_language_detection.py"
```

---

## Stage 1 Scope Guard (Must Not Be Added)

- No extraction router
- No extraction strategies package
- No extraction ledger
- No `ExtractedDocument` or LDU implementation
- No Stage 2 extraction workflow tasks

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independent test criteria.
4. Stop for MVP review.

### Incremental Delivery

1. Add US2 for deterministic persistence/evidence guarantees.
2. Add US3 for domain + language classification.
3. Complete graph runner polish and full suite validation.

### Suggested MVP Scope

- **Recommended MVP**: US1 only (graph-first triage classification + profile output).
