# Feature Specification: Query Agent and Provenance Layer

**Feature Branch**: `005-query-agent-provenance`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Build the Query Agent and Provenance Layer of the document intelligence pipeline. This stage must provide the front-end interface that allows users to ask natural language questions about processed documents and receive answers grounded in source evidence. The agent must use three tools: - pageindex_navigate - semantic_search - structured_query The goals of this stage are to: - answer user questions using the most appropriate retrieval path - navigate large documents efficiently without searching the entire corpus blindly - support precise querying of extracted numerical and structured facts - return every answer with explicit provenance - verify claims through an audit mode that determines whether a claim is supported, not found, or unverifiable Every answer must include a ProvenanceChain containing: - document_name - page_number - bounding_box - content_hash This stage must also support a FactTable for financial and numerical documents so that key-value facts can be queried precisely through SQL rather than only semantic search. Audit Mode must accept a claim and either: - verify it with source-backed provenance - mark it as not found - mark it as unverifiable This feature is limited to the Query Agent and Provenance Layer only. Do not include earlier-stage extraction, chunking, or PageIndex construction work."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask Grounded Questions (Priority: P1)

A user asks a natural-language question about a processed document and receives a direct answer that is grounded in the most relevant source evidence rather than a generic summary.

**Why this priority**: Answering grounded questions is the core user-facing capability of the stage and is the minimum valuable slice for downstream retrieval workflows.

**Independent Test**: Can be fully tested by asking a question against a processed document and confirming that the returned answer includes explicit provenance for every factual claim.

**Acceptance Scenarios**:

1. **Given** a processed document with a PageIndex and retrieval-ready chunks, **When** a user asks a question about a topic described in the document, **Then** the system returns an answer grounded in retrieved evidence and includes a ProvenanceChain for the supporting source content.
2. **Given** a large document with multiple sections, **When** a user asks a section-specific question, **Then** the system narrows to the most relevant sections before deeper retrieval and does not search the full document blindly.

---

### User Story 2 - Query Structured Facts Precisely (Priority: P2)

A user asks for a numerical or key-value fact from a financial or structured document and receives a precise answer drawn from a queryable fact representation rather than only semantic retrieval.

**Why this priority**: Numerical and tabular documents require precise retrieval behavior to avoid fuzzy or approximate answers for amounts, dates, ratios, or named fields.

**Independent Test**: Can be fully tested by querying a known financial or numerical fact and confirming that the system routes to structured fact retrieval, returns the exact value, and cites provenance.

**Acceptance Scenarios**:

1. **Given** a processed financial or numerical document with extracted facts, **When** a user asks for a specific key-value fact or numeric result, **Then** the system uses structured retrieval when appropriate and returns the exact fact with provenance.
2. **Given** a question that combines a narrative request with a numeric fact lookup, **When** the agent selects a retrieval path, **Then** it may combine section navigation, semantic retrieval, and structured fact retrieval while still returning a single grounded answer.

---

### User Story 3 - Verify Claims in Audit Mode (Priority: P3)

A user submits a claim about a document and receives an audit result that classifies the claim as supported, not found, or unverifiable based on source-backed evidence.

**Why this priority**: Audit mode is critical for trust, verification workflows, and high-stakes document use cases where unsupported claims must not be presented as confirmed.

**Independent Test**: Can be fully tested by submitting one supported claim, one absent claim, and one ambiguous claim and confirming that each receives the correct audit status and provenance handling.

**Acceptance Scenarios**:

1. **Given** a claim that is explicitly supported by document evidence, **When** a user runs audit mode, **Then** the system marks the claim as supported and returns the supporting provenance chain.
2. **Given** a claim that is not present in the document, **When** a user runs audit mode, **Then** the system marks the claim as not found and does not fabricate support.
3. **Given** a claim that cannot be confirmed from available evidence, **When** a user runs audit mode, **Then** the system marks the claim as unverifiable and explains that available evidence is insufficient.

### Edge Cases

- How does the system respond when multiple sections contain partially relevant evidence but none fully answer the question?
- What happens when a structured fact is requested from a document that has no queryable FactTable?
- How does audit mode behave when retrieved evidence is contradictory across sections or document elements?
- What happens when provenance metadata is incomplete for an otherwise relevant chunk or fact?
- How does the system respond when the user asks a broad question that spans multiple sections, tables, and figures?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a front-end query interface for asking natural-language questions about processed documents.
- **FR-002**: The system MUST support three retrieval tools for query execution: `pageindex_navigate`, `semantic_search`, and `structured_query`.
- **FR-003**: The system MUST select the most appropriate retrieval path for a question based on the question intent and the available processed document artifacts.
- **FR-004**: The system MUST use section navigation to narrow retrieval scope before deeper retrieval when a document is large enough or structurally complex enough to benefit from targeted navigation.
- **FR-005**: The system MUST support semantic retrieval over processed document content for narrative and descriptive questions.
- **FR-006**: The system MUST support structured fact retrieval for financial, numerical, and key-value questions when a queryable FactTable is available.
- **FR-007**: The system MUST return every answer with an explicit ProvenanceChain.
- **FR-008**: Each ProvenanceChain entry MUST include `document_name`, `page_number`, `bounding_box`, and `content_hash`.
- **FR-009**: The system MUST preserve source traceability between query results and the underlying processed document artifacts.
- **FR-010**: The system MUST support a FactTable representation for financial and numerical documents so that facts can be queried precisely rather than only semantically.
- **FR-011**: The system MUST support Audit Mode as a distinct query path that evaluates a user-provided claim against document evidence.
- **FR-012**: Audit Mode MUST classify each claim as exactly one of: `supported`, `not found`, or `unverifiable`.
- **FR-013**: The system MUST return source-backed provenance for supported audit findings.
- **FR-014**: The system MUST explicitly state when evidence is not found or insufficient instead of inferring unsupported answers.
- **FR-015**: The system MUST fail closed when retrieval results cannot satisfy the provenance requirement for an answer or audit finding.
- **FR-016**: The system MUST keep Query Agent behavior scoped to question answering, structured fact retrieval, provenance, and audit outcomes, without rebuilding earlier-stage extraction, chunking, or PageIndex artifacts.

## Constitution Alignment *(mandatory)*

### Non-Negotiable Invariants

- **CI-001 Typed Contracts**: The Query Agent, FactTable, audit result, answer payload, tool inputs, tool outputs, and ProvenanceChain MUST use explicit typed models; no raw provider or retrieval payload may cross stage boundaries.
- **CI-001a Provider Normalization**: Retrieval tools and any model-backed answer synthesis MUST normalize intermediate outputs into canonical query-stage contracts before orchestration continues.
- **CI-002 Provenance**: Every returned answer and every supported audit result MUST include validated provenance entries with `document_name`, `page_number`, `bounding_box`, and `content_hash`, and unsupported outcomes MUST explicitly state why provenance could not be established.
- **CI-003 Escalation Guard**: Query routing MUST prefer deterministic tool selection and fail closed when the chosen retrieval path cannot produce grounded evidence; unsupported or low-confidence results MUST not be silently passed downstream.
- **CI-004 Deterministic Chunking**: This feature MUST consume existing Stage 3 and Stage 4 artifacts as inputs and MUST NOT redefine earlier chunking behavior.
- **CI-005 Cost Controls**: Query execution SHOULD minimize expensive synthesis by narrowing sections first, using structured retrieval for exact facts, and avoiding unnecessary broad-context generation.
- **CI-006 Observability**: The stage MUST emit auditable query artifacts or logs that record the selected retrieval path, evidence set, outcome classification, and rule or mode references needed for diagnostics.
- **CI-007 Separation of Concerns**: The query agent MUST orchestrate tool use, retrieval tools MUST perform bounded retrieval work, typed models MUST define answer and provenance contracts, and validation logic MUST remain modular.
- **CI-008 Operability**: The stage MUST expose actionable failure categories for missing evidence, missing facts, insufficient provenance, and unverifiable claims, and it MUST remain operable without re-running earlier pipeline stages.

### Key Entities *(include if feature involves data)*

- **QueryRequest**: A user-issued question or claim, including the query text, requested mode, and target document context.
- **QueryAnswer**: The grounded answer returned to the user, including answer text, retrieval path used, and provenance chain.
- **ProvenanceChain**: The ordered source evidence attached to an answer or audit finding, including document name, page number, bounding box, and content hash.
- **FactTable**: A queryable collection of structured financial or numerical facts derived from processed documents for precise retrieval.
- **AuditResult**: The claim verification outcome, including classification (`supported`, `not found`, or `unverifiable`), explanation, and provenance when available.

## Assumptions

- Users submit queries only after a document has already been processed through earlier pipeline stages and retrieval-ready artifacts exist.
- The Query Agent can access prior-stage artifacts such as PageIndex data, retrieval-ready chunks, and structured facts without rebuilding them.
- Questions may target either narrative content or exact facts, so the system needs multiple retrieval paths within the same stage.
- Provenance is a mandatory part of the returned result, not an optional debug view.
- When a FactTable is unavailable for a document, the system may still answer by navigation and semantic retrieval if the answer can be grounded.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For supported questions against processed documents, 100% of returned answers include at least one provenance entry with document name, page number, bounding box, and content hash.
- **SC-002**: For documents with meaningful section structure, the system narrows retrieval to a smaller relevant section set before deep retrieval in at least 90% of section-targetable queries.
- **SC-003**: For structured financial or numerical fact questions where the fact exists in a queryable fact representation, users receive the exact requested fact with provenance in at least 95% of validation scenarios.
- **SC-004**: Audit mode correctly classifies supported, not-found, and unverifiable claims in at least 95% of validation scenarios without presenting unsupported claims as verified.
