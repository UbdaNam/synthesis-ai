# Research: Query Agent and Provenance Layer

## Decision: Use a LangGraph StateGraph with an explicit query state and a dedicated tool-execution loop

**Rationale**: LangGraph is already the project architecture, and the query layer needs multi-step tool use with explicit state updates before final synthesis. A `StateGraph` with an LLM node, a `ToolNode`-style execution node, and a typed finalize node keeps tool calls observable and testable while preserving deterministic routing hints outside the model.

**Alternatives considered**:
- A single LangChain agent executor: rejected because state transitions and failure modes are harder to validate against the constitution requirements.
- A custom imperative loop without LangGraph: rejected because it would diverge from the existing project architecture.

## Decision: Attach exactly three LangChain-compatible tools to an OpenRouter-backed chat model

**Rationale**: The feature explicitly requires `pageindex_navigate`, `semantic_search`, and `structured_query` as the only attached tools. OpenRouter provides the model gateway already used in the project, and a tool-calling model accessed through `langchain_openrouter.ChatOpenRouter` preserves a consistent provider boundary.

**Alternatives considered**:
- Adding helper tools beyond the required three: rejected because the spec constrains the tool surface and broader tool sets complicate routing and validation.
- Direct OpenAI runtime usage: rejected because the current project is already moving model-backed operations through OpenRouter.

## Decision: Use typed final response models with provenance validation and fail-closed synthesis

**Rationale**: The constitution requires typed contracts and prohibits unsupported answers without provenance. A final typed `QueryResult` model with explicit `support_status`, `retrieval_path_used`, and `provenance_chain` lets the finalize step reject invalid outputs instead of silently emitting partial answers.

**Alternatives considered**:
- Free-form final text with post-hoc regex parsing: rejected because it is brittle and not appropriate for provenance enforcement.
- Returning tool output directly: rejected because the user-facing stage still needs normalized answer and audit contracts.

## Decision: Use PageIndex JSON plus deterministic ranking for `pageindex_navigate`

**Rationale**: Stage 4 already persists PageIndex artifacts with section titles, summaries, entities, and page ranges. The navigation tool can read those JSON artifacts, rank relevant sections deterministically, and return narrowed search targets before semantic retrieval.

**Alternatives considered**:
- Regenerating section navigation from LDUs at query time: rejected because it would duplicate Stage 4 responsibilities.
- LLM-only navigation decisions: rejected because the section-ranking heuristics are measurable and should remain deterministic first.

## Decision: Reuse ChromaDB for `semantic_search` with metadata filters derived from section navigation

**Rationale**: Stage 4 already persists LDUs into a local Chroma collection with section-aware metadata. Reusing that store avoids duplicate indexing infrastructure and supports narrowing retrieval to specific sections before chunk search.

**Alternatives considered**:
- Rebuilding a new vector store just for Stage 5: rejected because it increases storage duplication and operational complexity.
- Pure lexical search over artifacts: rejected because narrative questions still need semantic retrieval.

## Decision: Store numerical and financial facts in SQLite with source linkage

**Rationale**: The spec requires precise SQL-based retrieval for FactTable queries. SQLite is available in the Python standard library, simple to persist locally, and sufficient for a document-scoped fact store when each row includes provenance linkage back to chunk IDs, page numbers, bounding boxes, and content hashes.

**Alternatives considered**:
- Keeping facts in JSON only: rejected because it would not satisfy the structured SQL query requirement.
- Using a remote relational database: rejected because the project currently operates on local persisted artifacts.

## Decision: Implement FactTable extraction deterministically from Stage 3 LDUs and Stage 4 section metadata

**Rationale**: Suitable numerical facts can be extracted from table chunks, key-value-like chunks, and high-signal numerical text patterns without requiring a model for every row. Deterministic extraction keeps fact generation testable and reproducible while preserving source linkage.

**Alternatives considered**:
- LLM-only fact extraction: rejected because the fact table needs high precision and deterministic tests.
- Skipping precomputation and generating ad hoc SQL rows at query time: rejected because it would slow query execution and blur stage boundaries.

## Decision: Treat Audit Mode as a separate module that reuses the same three tools and enforces closed-world outcomes

**Rationale**: Audit Mode needs the same retrieval infrastructure as standard question answering but a stricter decision contract. A dedicated module can classify claim status as `supported`, `not_found`, or `unverifiable` after tool use while reusing shared provenance validation.

**Alternatives considered**:
- Embedding audit behavior directly into the main answer path without a separate module: rejected because it weakens separation of concerns and makes classification harder to test.
- Returning probabilistic confidence scores instead of discrete statuses: rejected because the spec explicitly requires three deterministic outcome classes.
