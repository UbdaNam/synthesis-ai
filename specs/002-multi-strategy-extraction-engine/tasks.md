# Tasks: Stage 2 Structure Extraction Layer

**Input**: Design documents from `/specs/002-multi-strategy-extraction-engine/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution-gated behavior requires unit, validation, regression, and integration coverage.

**Organization**: Tasks are grouped by user story so each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependency conflict)
- **[Story]**: Story label required only in user-story phases
- Exact file paths are included in every task

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Stage 2 structure and baseline tooling/config

- [X] T001 Create Stage 2 source files in `src/models/extracted_document.py`, `src/agents/extractor.py`, `src/strategies/base.py`, `src/strategies/fast_text.py`, `src/strategies/layout_aware.py`, `src/strategies/vision.py`
- [X] T002 Add Stage 2 dependency declarations (`langchain-openrouter`, `python-dotenv`, `pymupdf`, optional layout provider deps) in `pyproject.toml`
- [X] T003 [P] Create strategy package export surface in `src/strategies/__init__.py`
- [X] T004 [P] Initialize extraction ledger artifact at `.refinery/extraction_ledger.jsonl`
- [X] T005 [P] Add Stage 2 test folders and placeholders in `tests/unit/` and `tests/integration/`
- [X] T006 [P] Add `.env.example` with OpenRouter keys in `.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contracts, state shape, and config prerequisites required before all user stories

**CRITICAL**: Complete this phase before any user story work

- [X] T007 Extend graph state with extraction fields in `src/models/graph_state.py`
- [X] T008 Implement normalized extraction models (`ExtractedDocument`, blocks, ledger/attempt models) in `src/models/extracted_document.py`
- [X] T009 Implement shared extraction strategy interface and result/context contracts in `src/strategies/base.py`
- [X] T010 Add extraction config sections (thresholds, escalation, vision, costing, rule version, layout provider) in `rubric/extraction_rules.yaml`
- [X] T011 Implement extractor agent skeleton with deterministic strategy registry in `src/agents/extractor.py`
- [X] T012 Wire extraction node into graph flow (`triage -> extract`) in `src/graph/graph.py`
- [X] T013 [P] Add shared Stage 2 fixtures/config fixture for tests in `tests/conftest.py`
- [X] T014 [P] Add foundational contract test coverage for extraction payload types in `tests/unit/test_stage2_contracts.py`
- [X] T015 [P] Add foundational graph-state contract test for extraction state transitions in `tests/unit/test_graph_state_extraction_contract.py`

**Checkpoint**: Foundation complete, user-story phases may begin

---

## Phase 3: User Story 1 - Route And Extract Structured Content (Priority: P1) MVP

**Goal**: Route to proper strategy and emit normalized `ExtractedDocument` from Stage 2

**Independent Test**: For representative native, complex-layout, and scanned inputs, verify `DocumentProfile -> router -> strategy -> normalized ExtractedDocument` with provenance fields.

### Tests for User Story 1

- [X] T016 [P] [US1] Add unit tests for deterministic initial strategy selection in `tests/unit/test_extraction_router_selection.py`
- [X] T017 [P] [US1] Add unit tests for FastText confidence signal scoring in `tests/unit/test_fast_text_confidence_scoring.py`
- [X] T018 [P] [US1] Add unit tests for ExtractedDocument schema validity and non-empty content rules in `tests/unit/test_extracted_document_schema.py`
- [X] T019 [P] [US1] Add unit tests for LayoutExtractor provider selection (`docling`/`mineru`) in `tests/unit/test_layout_provider_selection.py`
- [X] T020 [P] [US1] Add unit tests for LayoutExtractor provider normalization into `ExtractedDocument` in `tests/unit/test_layout_provider_normalization.py`
- [X] T021 [P] [US1] Add integration test for profile-to-normalized-output flow in `tests/integration/test_extraction_normalization_flow.py`
- [X] T022 [P] [US1] Add integration test for graph execution with extraction node in `tests/integration/test_graph_with_extraction_node.py`

### Implementation for User Story 1

- [X] T023 [P] [US1] Implement Strategy A text extraction and normalization in `src/strategies/fast_text.py`
- [X] T024 [P] [US1] Implement Strategy B LayoutExtractor using **one provider path (Docling or MinerU)** plus provider adapter interface in `src/strategies/layout_aware.py`
- [X] T025 [P] [US1] Add explicit layout provider configuration key (`layout_aware.provider: docling|mineru`) and adapter settings in `rubric/extraction_rules.yaml`
- [X] T026 [P] [US1] Implement Strategy C base normalization pipeline in `src/strategies/vision.py`
- [X] T027 [US1] Implement deterministic initial routing from `DocumentProfile` in `src/agents/extractor.py`
- [X] T028 [US1] Implement state update behavior for accepted extraction output in `src/agents/extractor.py`
- [X] T029 [US1] Implement provenance population (`page_number`, `bounding_box`, `content_hash`) across all strategies in `src/strategies/fast_text.py`, `src/strategies/layout_aware.py`, `src/strategies/vision.py`
- [X] T030 [US1] Add JSON-schema compatibility test for extracted payload contract in `tests/unit/test_extracted_document_schema_contract.py`

**Checkpoint**: US1 is independently functional (MVP)

---

## Phase 4: User Story 2 - Enforce Escalation Guard (Priority: P2)

**Goal**: Enforce confidence-gated A->B->C escalation, including vision triggers and fail-closed behavior

**Independent Test**: Force low-confidence A/B attempts and verify deterministic escalation to stronger strategy; verify fail-closed on final threshold failure or budget cap violation.

### Tests for User Story 2

- [X] T031 [P] [US2] Add unit test for A low-confidence escalation to B in `tests/unit/test_escalation_a_to_b.py`
- [X] T032 [P] [US2] Add unit test for B low-confidence escalation to C in `tests/unit/test_escalation_b_to_c.py`
- [X] T033 [P] [US2] Add unit test for fail-closed after C below threshold in `tests/unit/test_escalation_fail_closed.py`
- [X] T034 [P] [US2] Add unit test for confidence threshold boundary behavior in `tests/unit/test_confidence_threshold_boundaries.py`
- [X] T035 [P] [US2] Add unit test for handwriting-detected trigger routing to vision in `tests/unit/test_handwriting_trigger_routing.py`
- [X] T036 [P] [US2] Add unit test for vision budget-cap enforcement in `tests/unit/test_vision_budget_cap.py`
- [X] T037 [P] [US2] Add integration test for escalation paths across A/B/C outcomes in `tests/integration/test_extraction_escalation_paths.py`
- [X] T038 [P] [US2] Add integration test for unreadable/corrupt input fail-closed behavior in `tests/integration/test_extraction_fail_closed_unreadable.py`

### Implementation for User Story 2

- [X] T039 [US2] Implement confidence gate evaluator and threshold checks in `src/agents/extractor.py`
- [X] T040 [US2] Implement deterministic escalation loop and terminal fail-closed handling in `src/agents/extractor.py`
- [X] T041 [US2] Implement Vision trigger conditions (`scanned_image`, low A/B confidence, handwriting) in `src/agents/extractor.py`
- [X] T042 [US2] Implement LangGraph-compatible Vision invocation with provider-enforced schema output (`with_structured_output`) in `src/strategies/vision.py`
- [X] T043 [US2] Implement per-document token accounting and cost estimation in `src/strategies/vision.py`
- [X] T044 [US2] Implement budget-cap guard and overflow fail-closed behavior in `src/strategies/vision.py` and `src/agents/extractor.py`
- [X] T045 [US2] Add/update escalation and vision budget config keys in `rubric/extraction_rules.yaml`

**Checkpoint**: US2 independently enforces escalation and budget controls

---

## Phase 5: User Story 3 - Provide Decision And Cost Auditability (Priority: P3)

**Goal**: Produce full strategy/cost/confidence/escalation audit trail per document

**Independent Test**: Process non-escalated and escalated docs; verify attempt-level ledger entries include required minimum fields plus budget and disposition context.

### Tests for User Story 3

- [X] T046 [P] [US3] Add unit tests for required ledger fields in `tests/unit/test_extraction_ledger_entry_fields.py`
- [X] T047 [P] [US3] Add unit tests for processing-time and cost metric correctness in `tests/unit/test_extraction_ledger_metrics.py`
- [X] T048 [P] [US3] Add unit test for ledger schema contract compatibility in `tests/unit/test_extraction_ledger_schema_contract.py`
- [X] T049 [P] [US3] Add integration test for escalation decision trace logging in `tests/integration/test_extraction_ledger_trace.py`

### Implementation for User Story 3

- [X] T050 [US3] Implement per-attempt ledger append operation in `src/agents/extractor.py`
- [X] T051 [US3] Implement ledger payload mapping for threshold/rule reference, escalation flag, and final disposition in `src/agents/extractor.py`
- [X] T052 [US3] Implement strategy-level cost estimation mapping for FastText in `src/strategies/fast_text.py`
- [X] T053 [US3] Implement strategy-level cost estimation mapping for Layout/Vision in `src/strategies/layout_aware.py` and `src/strategies/vision.py`
- [X] T054 [US3] Add usage token and budget fields to ledger emission path in `src/agents/extractor.py`

**Checkpoint**: US3 independently delivers auditable decision and cost traceability

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Determinism, documentation, and final hardening across stories

- [X] T055 [P] Add deterministic repeatability regression for extraction routing in `tests/unit/test_extraction_deterministic_routing.py`
- [X] T056 [P] Add chunking invariants validation tests for deterministic structural boundaries in `tests/unit/test_chunking_invariants.py`
- [X] T057 [P] Add regression test for known extraction failure scenario in `tests/integration/test_extraction_regression_known_failure.py`
- [X] T058 [P] Update Stage 2 usage/configuration docs in `README.md`
- [X] T059 Harden typed error normalization and failure reason taxonomy in `src/agents/extractor.py`
- [X] T060 Tune default extraction thresholds and budget values in `rubric/extraction_rules.yaml`
- [X] T061 Validate quickstart flow and update command notes in `specs/002-multi-strategy-extraction-engine/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 2 and shares router interfaces with US1
- **Phase 5 (US3)**: Depends on Phase 2 and consumes router/strategy attempt outputs
- **Phase 6 (Polish)**: Depends on completion of targeted stories

### User Story Completion Order

1. **US1 (P1)** MVP first
2. **US2 (P2)** escalation and reliability controls
3. **US3 (P3)** auditability and cost traceability

### Parallel Opportunities

- Setup parallel: T003-T006
- Foundational parallel: T013-T015
- US1 parallel tests: T016-T022
- US1 parallel implementation: T023-T026
- US2 parallel tests: T031-T038
- US3 parallel tests: T046-T049
- Polish parallel: T055-T058

---

## Parallel Example: User Story 1

```bash
Task: "T016 [US1] tests/unit/test_extraction_router_selection.py"
Task: "T019 [US1] tests/unit/test_layout_provider_selection.py"
Task: "T021 [US1] tests/integration/test_extraction_normalization_flow.py"

Task: "T023 [US1] src/strategies/fast_text.py"
Task: "T024 [US1] src/strategies/layout_aware.py"
Task: "T026 [US1] src/strategies/vision.py"
```

## Parallel Example: User Story 2

```bash
Task: "T031 [US2] tests/unit/test_escalation_a_to_b.py"
Task: "T035 [US2] tests/unit/test_handwriting_trigger_routing.py"
Task: "T036 [US2] tests/unit/test_vision_budget_cap.py"

Task: "T042 [US2] src/strategies/vision.py"
Task: "T045 [US2] rubric/extraction_rules.yaml"
```

## Parallel Example: User Story 3

```bash
Task: "T046 [US3] tests/unit/test_extraction_ledger_entry_fields.py"
Task: "T047 [US3] tests/unit/test_extraction_ledger_metrics.py"
Task: "T049 [US3] tests/integration/test_extraction_ledger_trace.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete US1 (Phase 3)
3. Validate US1 independent test criteria
4. Demo/deploy MVP

### Incremental Delivery

1. Deliver US1 baseline extraction
2. Add US2 escalation and budget guard controls
3. Add US3 audit and cost traceability
4. Complete polish for deterministic validation and regression hardening

### Parallel Team Strategy

1. Complete Setup + Foundational together
2. Split by story after Phase 2:
   - Engineer A: US1 strategy and normalization
   - Engineer B: US2 escalation and vision budget/trigger logic
   - Engineer C: US3 ledgering and audit tests
3. Rejoin for Phase 6 hardening
