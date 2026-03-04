# Tasks: Triage Agent Document Profiling

**Input**: Design documents from `/specs/001-triage-document-profile/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included because the specification explicitly requires unit tests, deterministic behavior, auditability, and evaluation validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label for story-phase tasks only (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an absolute file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize code/test structure and dependencies for Stage 1.

- [ ] T001 Create Stage 1 package directories in `C:\Abdu\synthesis-ai\src\synthesis_ai\models\`, `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\`, `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\domain\`, and `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\`
- [ ] T002 [P] Create Stage 1 test and fixture directories in `C:\Abdu\synthesis-ai\tests\unit\` and `C:\Abdu\synthesis-ai\tests\fixtures\pdf_samples\`
- [ ] T003 Update dependencies in `C:\Abdu\synthesis-ai\pyproject.toml` to include `pydantic`, `langgraph`, `pytest`, and a lightweight deterministic language detection library
- [ ] T004 Create package initialization files in `C:\Abdu\synthesis-ai\src\synthesis_ai\__init__.py`, `C:\Abdu\synthesis-ai\src\synthesis_ai\models\__init__.py`, `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\__init__.py`, `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\domain\__init__.py`, and `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core typed contracts and shared primitives required by all stories.

**CRITICAL**: No user story work starts before this phase is complete.

- [ ] T005 Implement typed `DocumentProfile` and nested models in `C:\Abdu\synthesis-ai\src\synthesis_ai\models\document_profile.py`
- [ ] T006 Implement typed `GraphState` model with optional `document_profile` in `C:\Abdu\synthesis-ai\src\synthesis_ai\models\graph_state.py`
- [ ] T007 Implement profile persistence utility for `.refinery/profiles/{doc_id}.json` in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profile_repository.py`
- [ ] T008 [P] Implement deterministic extraction-cost mapping rules in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\extraction_cost_resolver.py`
- [ ] T009 [P] Implement shared deterministic thresholds/config constants in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\config.py`
- [ ] T010 Implement profiling ledger writer for `.refinery/profiling_ledger.jsonl` in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profiling_logger.py`
- [ ] T011 [P] Implement profiling ledger entry schema/formatter in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profiling_ledger_schema.py`

**Checkpoint**: Foundation ready for independent user story implementation.

---

## Phase 3: User Story 1 - Route Extraction by Document Type (Priority: P1) MVP

**Goal**: Deterministically classify document origin/layout and route extraction cost.

**Independent Test**: Run triage on representative native/scanned/mixed/form-fillable samples and verify `origin_type`, `layout_complexity`, and `estimated_extraction_cost` are correct.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add PDF stats analyzer unit tests for char count, char density, image ratio, font metadata, and bbox signals in `C:\Abdu\synthesis-ai\tests\unit\test_pdf_stats_analyzer.py`
- [ ] T013 [P] [US1] Add origin classification unit tests in `C:\Abdu\synthesis-ai\tests\unit\test_origin_classifier.py`
- [ ] T014 [P] [US1] Add layout classification unit tests in `C:\Abdu\synthesis-ai\tests\unit\test_layout_classifier.py`
- [ ] T015 [P] [US1] Add extraction-cost resolver unit tests in `C:\Abdu\synthesis-ai\tests\unit\test_extraction_cost_resolver.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement `PDFStatsAnalyzer` with pdfplumber metric extraction in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\pdf_stats_analyzer.py`
- [ ] T017 [US1] Implement `OriginClassifier` (`native_digital|scanned_image|mixed|form_fillable`) in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\origin_classifier.py`
- [ ] T018 [US1] Implement `LayoutClassifier` (x-clustering, grid alignment, figure-heavy logic) in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\layout_classifier.py`
- [ ] T019 [US1] Implement first-node LangGraph triage node orchestration in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_node.py`
- [ ] T020 [US1] Integrate analyzer + origin + layout + cost resolver into graph node flow in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_node.py`

**Checkpoint**: US1 independently classifies and routes documents.

---

## Phase 4: User Story 2 - Preserve Deterministic Typed Output (Priority: P2)

**Goal**: Persist schema-valid, deterministic profiles and auditable observability logs.

**Independent Test**: Run triage repeatedly on same document and verify identical profile output, schema validity, and correctly formatted profiling ledger entries.

### Tests for User Story 2

- [ ] T021 [P] [US2] Add deterministic repeatability test (`same document -> identical DocumentProfile`) in `C:\Abdu\synthesis-ai\tests\unit\test_determinism.py`
- [ ] T022 [P] [US2] Add JSON schema validation test for `DocumentProfile` in `C:\Abdu\synthesis-ai\tests\unit\test_document_profile_schema.py`
- [ ] T023 [P] [US2] Add serialization consistency test for profile persistence in `C:\Abdu\synthesis-ai\tests\unit\test_document_profile_serialization.py`
- [ ] T024 [P] [US2] Add profiling ledger format test in `C:\Abdu\synthesis-ai\tests\unit\test_profiling_ledger_format.py`
- [ ] T025 [P] [US2] Add profiling processing-time recording test in `C:\Abdu\synthesis-ai\tests\unit\test_profiling_processing_time.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement idempotent profile JSON persistence behavior in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profile_repository.py`
- [ ] T027 [US2] Implement deterministic profile serialization helper in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\serialization.py`
- [ ] T028 [US2] Implement observability logging of computed classification signals (`char_density`, `image_ratio`, layout signals) in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profiling_logger.py`
- [ ] T029 [US2] Implement processing-time capture per document in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\profiling_logger.py`
- [ ] T030 [US2] Wire profile persistence + profiling ledger write into triage completion path in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_node.py`

**Checkpoint**: US2 independently guarantees deterministic typed output + observability ledger compliance.

---

## Phase 5: User Story 3 - Support Domain-Aware and Language-Aware Routing Policies (Priority: P3)

**Goal**: Provide pluggable domain strategy and deterministic language detection with confidence.

**Independent Test**: Validate allowed domain outputs and deterministic language code+confidence on English and non-English samples.

### Tests for User Story 3

- [ ] T031 [P] [US3] Add domain strategy interface behavior tests in `C:\Abdu\synthesis-ai\tests\unit\test_domain_strategy.py`
- [ ] T032 [P] [US3] Add keyword domain scoring tests in `C:\Abdu\synthesis-ai\tests\unit\test_domain_classifier.py`
- [ ] T033 [P] [US3] Add language detection unit tests for English sample in `C:\Abdu\synthesis-ai\tests\unit\test_language_detector.py`
- [ ] T034 [P] [US3] Add language detection unit tests for non-English sample in `C:\Abdu\synthesis-ai\tests\unit\test_language_detector.py`
- [ ] T035 [P] [US3] Add language confidence scoring + determinism tests in `C:\Abdu\synthesis-ai\tests\unit\test_language_detector.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `DomainClassifierStrategy` interface in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\domain\strategy.py`
- [ ] T037 [US3] Implement keyword-based domain classifier in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\domain\keyword_strategy.py`
- [ ] T038 [US3] Implement language detection module returning `code` + `confidence` in `C:\Abdu\synthesis-ai\src\synthesis_ai\triage\language_detector.py`
- [ ] T039 [US3] Integrate domain + language detection into triage output assembly in `C:\Abdu\synthesis-ai\src\synthesis_ai\graph\triage_node.py`

**Checkpoint**: US3 independently delivers domain + language requirements.

---

## Phase 6: Evaluation & Cross-Cutting Validation

**Purpose**: Validate success criteria, constitution auditability, and end-to-end readiness.

- [ ] T040 [P] Add known-document classification validation suite in `C:\Abdu\synthesis-ai\tests\unit\test_known_samples_accuracy.py`
- [ ] T041 [P] Add success-criteria validation test for routing quality targets in `C:\Abdu\synthesis-ai\tests\unit\test_routing_quality.py`
- [ ] T042 Add end-to-end Stage 1 smoke test including profile + ledger assertions in `C:\Abdu\synthesis-ai\tests\unit\test_triage_end_to_end.py`
- [ ] T043 [P] Update Stage 1 usage documentation with observability outputs in `C:\Abdu\synthesis-ai\README.md`
- [ ] T044 Run and stabilize full Stage 1 unit test suite in `C:\Abdu\synthesis-ai\tests\`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; recommended MVP.
- **Phase 4 (US2)**: Depends on US1 baseline pipeline.
- **Phase 5 (US3)**: Depends on US1 baseline pipeline.
- **Phase 6 (Evaluation/Polish)**: Depends on US1 + US2 + US3 completion.

### User Story Dependencies

- **US1 (P1)**: Starts after foundational phase.
- **US2 (P2)**: Depends on US1 triage flow and adds observability + deterministic persistence.
- **US3 (P3)**: Depends on US1 flow and adds domain/language behavior.

### Dependency Graph

`Setup -> Foundational -> US1 -> (US2 || US3) -> Evaluation/Polish`

---

## Parallel Execution Opportunities

- **Setup**: `T002` and `T004` can run in parallel after `T001`.
- **Foundational**: `T008`, `T009`, `T011` can run in parallel after `T005-T007/T010` decisions are fixed.
- **US1**: `T012-T015` can run in parallel; then `T016-T018` can run in parallel before `T019-T020`.
- **US2**: `T021-T025` can run in parallel; `T026-T029` can run in parallel before `T030`.
- **US3**: `T031-T035` can run in parallel; `T036-T038` can run in parallel before `T039`.
- **Evaluation**: `T040`, `T041`, `T043` can run in parallel before `T042` and `T044`.

## Parallel Example: User Story 1

```text
Task: "T012 [US1] Add PDF stats analyzer unit tests in C:\Abdu\synthesis-ai\tests\unit\test_pdf_stats_analyzer.py"
Task: "T013 [US1] Add origin classification unit tests in C:\Abdu\synthesis-ai\tests\unit\test_origin_classifier.py"
Task: "T014 [US1] Add layout classification unit tests in C:\Abdu\synthesis-ai\tests\unit\test_layout_classifier.py"
Task: "T015 [US1] Add extraction-cost resolver unit tests in C:\Abdu\synthesis-ai\tests\unit\test_extraction_cost_resolver.py"
```

## Parallel Example: User Story 2

```text
Task: "T021 [US2] Add deterministic repeatability test in C:\Abdu\synthesis-ai\tests\unit\test_determinism.py"
Task: "T022 [US2] Add JSON schema validation test in C:\Abdu\synthesis-ai\tests\unit\test_document_profile_schema.py"
Task: "T024 [US2] Add profiling ledger format test in C:\Abdu\synthesis-ai\tests\unit\test_profiling_ledger_format.py"
Task: "T025 [US2] Add processing-time recording test in C:\Abdu\synthesis-ai\tests\unit\test_profiling_processing_time.py"
```

## Parallel Example: User Story 3

```text
Task: "T033 [US3] Add language detection unit tests for English sample in C:\Abdu\synthesis-ai\tests\unit\test_language_detector.py"
Task: "T034 [US3] Add language detection unit tests for non-English sample in C:\Abdu\synthesis-ai\tests\unit\test_language_detector.py"
Task: "T035 [US3] Add language confidence determinism tests in C:\Abdu\synthesis-ai\tests\unit\test_language_detector.py"
Task: "T031 [US3] Add domain strategy interface tests in C:\Abdu\synthesis-ai\tests\unit\test_domain_strategy.py"
```

---

## Requirement-to-Task Mapping (Explicit Alignment)

- **Language detection requirement (FR-004, FR-018)**: `T033`, `T034`, `T035`, `T038`, `T039`
- **Observability requirement (FR-015, FR-017)**: `T010`, `T011`, `T024`, `T028`, `T029`, `T030`, `T042`
- **Constitution auditability principles (VI, Delivery Gate)**: `T010`, `T011`, `T024`, `T028`, `T029`, `T040`, `T042`, `T044`
- **Success criteria validation (SC-001, SC-002, SC-003, SC-004)**: `T021`, `T022`, `T023`, `T040`, `T041`, `T044`

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independent test criteria on known core samples.
4. Stop for MVP review.

### Incremental Delivery

1. Add US2 for deterministic persistence and profiling observability ledger.
2. Add US3 for pluggable domain + deterministic language detection.
3. Complete Phase 6 evaluation suite and final stabilization.

### Suggested MVP Scope

- **Recommended MVP**: US1 only (origin/layout/cost routing in first LangGraph node).
