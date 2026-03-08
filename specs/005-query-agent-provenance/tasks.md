# Tasks: Query Agent and Provenance Layer

**Input**: Design documents from `/specs/005-query-agent-provenance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include test tasks whenever constitution-gated behavior is implemented.
Unit, validation, and regression tests are mandatory for governed pipeline changes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project based on the selected structure in plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Stage 5 scaffolding

- [X] T001 Create the Stage 5 query package structure in src/agents/query_agent.py, src/models/provenance_chain.py, src/models/query_result.py, src/query/fact_table_extractor.py, src/query/audit_mode.py, and src/query/tools/
- [X] T002 [P] Add Stage 5 query configuration placeholders for OpenRouter model, Chroma collection access, SQLite fact storage, and query-stage settings in rubric/extraction_rules.yaml
- [X] T003 [P] Document Stage 5 environment variables and local storage paths for the query layer in .env.example and README.md
- [X] T004 [P] Add Stage 5 artifact directories for SQLite facts and any query-stage persisted outputs in .gitignore and runtime setup paths under .refinery/query/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared contracts, state extensions, and retrieval infrastructure required before user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Define the ProvenanceChain item schema with document_name, page_number, bounding_box, and content_hash validation in src/models/provenance_chain.py
- [X] T006 Define the final query result, query request, audit result, and retrieval-path enums with fail-closed provenance rules in src/models/query_result.py
- [X] T007 Extend shared graph/query state contracts for QueryRequest, QueryResult, navigation candidates, semantic hits, structured rows, query errors, and query metadata in src/models/graph_state.py
- [X] T008 [P] Implement shared query-stage utility types and normalization helpers for tool outputs in src/query/__init__.py and src/query/tools/__init__.py
- [X] T009 Implement SQLite FactTable schema creation, connection management, and persistence helpers in src/query/fact_table_extractor.py
- [X] T010 Implement Chroma access helpers and metadata normalization for query-stage semantic retrieval in src/query/tools/semantic_search.py
- [X] T011 Implement PageIndex artifact loading and deterministic section candidate normalization in src/query/tools/pageindex_navigate.py
- [X] T012 Implement shared SQL result normalization and provenance linkage helpers in src/query/tools/structured_query.py
- [X] T013 [P] Add foundational unit tests for provenance schema validation and final result schema validation in tests/unit/test_provenance_chain.py and tests/unit/test_query_result_schema.py
- [X] T014 [P] Add foundational unit tests for SQLite FactTable schema creation and row persistence in tests/unit/test_fact_table_extractor.py

---

## Phase 3: User Story 1 - Ask Grounded Questions (Priority: P1)

**Goal**: Answer natural-language questions with grounded provenance using a real LangGraph tool-calling agent

**Independent Test**: Ask a narrative question against a processed document and confirm the agent uses the required tools, narrows retrieval when appropriate, and returns a supported answer with a valid ProvenanceChain.

### Tests for User Story 1

- [X] T015 [P] [US1] Add unit tests for pageindex_navigate tool ranking over persisted PageIndex artifacts in tests/unit/test_pageindex_navigate_tool.py
- [X] T016 [P] [US1] Add unit tests for semantic_search tool behavior over the local Chroma collection with section filters in tests/unit/test_semantic_search_tool.py
- [X] T017 [P] [US1] Add unit tests for provenance-aware final answer formatting and fail-closed supported-answer validation in tests/unit/test_query_answer_formatting.py
- [X] T018 [P] [US1] Add integration tests for natural-language question -> tool calls -> final answer with provenance in tests/integration/test_query_agent_grounded_answer.py
- [X] T019 [P] [US1] Add integration tests for section-first retrieval path using pageindex_navigate before semantic_search in tests/integration/test_query_agent_section_first.py

### Implementation for User Story 1

- [X] T020 [US1] Implement the real pageindex_navigate tool over persisted PageIndex JSON artifacts in src/query/tools/pageindex_navigate.py
- [X] T021 [US1] Implement the real semantic_search tool over the existing local Chroma vector database in src/query/tools/semantic_search.py
- [X] T022 [US1] Implement provenance-aware result assembly helpers that convert navigation and semantic hits into validated provenance entries in src/models/provenance_chain.py and src/models/query_result.py
- [X] T023 [US1] Implement the LangGraph query agent entrypoint with explicit shared state updates in src/agents/query_agent.py
- [X] T024 [US1] Attach exactly three tools to the OpenRouter-backed tool-calling model in src/agents/query_agent.py
- [X] T025 [US1] Implement the multi-step tool execution loop and final typed answer synthesis path in src/agents/query_agent.py
- [X] T026 [US1] Record retrieval_path_used, matched sections, and structured failure categories in query-stage state updates in src/agents/query_agent.py and src/models/graph_state.py

---

## Phase 4: User Story 2 - Query Structured Facts Precisely (Priority: P2)

**Goal**: Answer financial and numerical questions through SQLite-backed fact retrieval with provenance

**Independent Test**: Ask an exact numerical question for a processed financial document and confirm the agent uses structured_query, returns the exact fact, and includes source-backed provenance.

### Tests for User Story 2

- [X] T027 [P] [US2] Add unit tests for structured_query SQL execution and provenance-bearing result normalization in tests/unit/test_structured_query_tool.py
- [X] T028 [P] [US2] Add unit tests for fact extraction from table and key-value LDUs into SQLite rows in tests/unit/test_fact_table_extractor_rows.py
- [X] T029 [P] [US2] Add integration tests for numerical question retrieval through structured_query in tests/integration/test_query_agent_structured_fact.py
- [X] T030 [P] [US2] Add integration tests for mixed retrieval where structured facts and semantic evidence are combined safely in tests/integration/test_query_agent_mixed_retrieval.py

### Implementation for User Story 2

- [X] T031 [US2] Implement deterministic FactTable extraction for financial and numerical facts with provenance linkage in src/query/fact_table_extractor.py
- [X] T032 [US2] Implement SQLite FactTable storage initialization and document-scoped fact loading in src/query/fact_table_extractor.py
- [X] T033 [US2] Implement the real structured_query tool over SQLite with query text parsing, SQL execution, and provenance-aware row output in src/query/tools/structured_query.py
- [X] T034 [US2] Add query-agent routing logic that prefers structured_query for fact-heavy and numerical requests in src/agents/query_agent.py
- [X] T035 [US2] Add final answer formatting logic that preserves exact fact values and matched fact IDs in src/models/query_result.py and src/agents/query_agent.py

---

## Phase 5: User Story 3 - Verify Claims in Audit Mode (Priority: P3)

**Goal**: Verify claims as supported, not_found, or unverifiable using the same real retrieval tools and fail-closed provenance rules

**Independent Test**: Submit one supported claim, one absent claim, and one ambiguous claim and confirm the system classifies each correctly with the required provenance behavior.

### Tests for User Story 3

- [X] T036 [P] [US3] Add unit tests for audit mode classification and fail-closed unsupported-answer handling in tests/unit/test_audit_mode.py
- [X] T037 [P] [US3] Add unit tests for query agent routing decisions across question_answering and audit modes in tests/unit/test_query_agent_routing.py
- [X] T038 [P] [US3] Add integration tests for audit-mode supported / not_found / unverifiable outcomes in tests/integration/test_query_agent_audit_mode.py

### Implementation for User Story 3

- [X] T039 [US3] Implement audit-mode claim evaluation using the shared retrieval tools in src/query/audit_mode.py
- [X] T040 [US3] Implement audit-mode result classification with supported, not_found, and unverifiable outcomes in src/query/audit_mode.py and src/models/query_result.py
- [X] T041 [US3] Integrate audit-mode execution into the LangGraph query agent flow in src/agents/query_agent.py
- [X] T042 [US3] Enforce that all supported answers and supported audit findings include a validated ProvenanceChain in src/models/query_result.py and src/agents/query_agent.py

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cross-cutting operational readiness

- [X] T043 [P] Add query-stage regression coverage for real infrastructure usage with persisted PageIndex, Chroma, and SQLite assets in tests/integration/test_query_agent_real_infrastructure.py
- [X] T044 Update README.md with Query Agent usage, audit mode behavior, ProvenanceChain requirements, and FactTable storage notes in README.md
- [X] T045 Update main.py or the next public runtime entrypoint to surface Stage 5 query execution and query errors clearly in main.py
- [X] T046 Run the Stage 5-focused test suite and capture the expected commands in specs/005-query-agent-provenance/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 completion; delivers the MVP grounded question-answering path.
- **Phase 4 (US2)**: Depends on Phase 2 completion and can build on US1 query-agent orchestration.
- **Phase 5 (US3)**: Depends on Phase 2 completion and reuses the retrieval surface established by US1 and US2.
- **Phase 6 (Polish)**: Depends on completion of the targeted user stories being shipped.

### User Story Dependencies

- **US1**: Independent MVP after Phase 2.
- **US2**: Depends on foundational contracts and the shared query-agent path from US1 for final answer emission.
- **US3**: Depends on foundational contracts and benefits from the shared retrieval and answer-validation paths from US1 and US2.

### Within Each User Story

- Write tests before implementation tasks where the same files are being introduced or changed.
- Implement models and tool boundaries before orchestration code that composes them.
- Keep tasks touching the same file sequential unless explicitly marked `[P]`.

## Parallel Execution Examples

### User Story 1

- Run `T015`, `T016`, and `T017` in parallel to cover navigation, semantic search, and result-format validation.
- Run `T018` and `T019` in parallel after the shared fixtures for Stage 5 integration tests are in place.

### User Story 2

- Run `T027` and `T028` in parallel because they cover different Stage 5 modules.
- Run `T029` and `T030` in parallel once `structured_query.py` and `fact_table_extractor.py` exist.

### User Story 3

- Run `T036` and `T037` in parallel because they target separate audit and routing concerns.
- Run `T038` after audit mode wiring is complete while `T043` remains reserved for broader regression coverage.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Deliver US1 so the project has a real LangGraph query agent that answers grounded narrative questions with provenance.
3. Validate the MVP with `test_query_agent_grounded_answer.py` and `test_query_agent_section_first.py`.

### Incremental Delivery

1. Add US2 to support exact numerical and financial fact retrieval through SQLite-backed structured queries.
2. Add US3 to support audit-mode claim verification using the same three-tool surface.
3. Finish with Phase 6 regression coverage and runtime documentation.

### Task Count Summary

- **Total tasks**: 46
- **Setup**: 4
- **Foundational**: 10
- **US1**: 12
- **US2**: 9
- **US3**: 7
- **Polish**: 4
