# Research: PageIndex Builder

## Decision 1: Build the section tree deterministically from Stage 3 LDUs

**Decision**: Construct the PageIndex hierarchy from validated Stage 3 `LDU`
ordering, `parent_section` metadata, and page references instead of using an
LLM to infer section structure.

**Rationale**: Stage 4 inherits a typed, validated Stage 3 contract. Using that
contract directly preserves determinism, keeps hierarchy construction testable,
and aligns with the constitution requirement that measurable logic remains
outside the LLM whenever possible.

**Alternatives considered**:

- Reconstruct hierarchy from raw extraction artifacts: rejected because Stage 4
  must consume only validated Stage 3 outputs.
- Ask an LLM to infer section nesting: rejected because heading and chunk-order
  signals are already measurable and deterministic.

## Decision 2: Use a typed PageIndex document wrapper with persisted JSON output

**Decision**: Represent Stage 4 output with a document-level PageIndex wrapper
containing typed section nodes and persist it as JSON under
`.refinery/pageindex/{doc_id}.json`.

**Rationale**: A document wrapper makes persistence, validation, and later
LangGraph state handoff explicit. Persisted JSON also satisfies auditability and
operability requirements while keeping downstream retrieval inputs inspectable.

**Alternatives considered**:

- Emit only a list of nodes in memory: rejected because persistence is a stated
  feature requirement.
- Persist ad hoc dictionaries: rejected because the constitution requires typed
  contracts at stage boundaries.

## Decision 3: Use rule-based entity extraction first

**Decision**: Implement key-entity extraction with deterministic pattern and
normalization rules first, with optional bounded refinement hooks kept outside
the baseline flow.

**Rationale**: Stage 4 needs deterministic enough outputs for testing and for
repeatable indexing. Rule-based extraction can capture names, identifiers,
financial terms, and domain labels from LDU content without introducing
unbounded model variance into the core indexing path.

**Alternatives considered**:

- Pure GPT entity extraction: rejected because it would weaken reproducibility
  and increase cost for a signal that is sufficiently measurable.
- No entity extraction: rejected because key entities are required outputs.

## Decision 4: Detect section data types from Stage 3 chunk metadata

**Decision**: Infer `data_types_present` from LDU `chunk_type` and chunk
metadata, normalizing to at least `tables`, `figures`, `equations`,
`narrative_text`, and `lists`.

**Rationale**: Stage 3 already encodes structural distinctions needed for this
classification. Reusing those signals is direct, deterministic, and easy to
validate.

**Alternatives considered**:

- Re-inspect original document content: rejected because Stage 4 should not step
  around Stage 3 contracts.
- Use an LLM classifier: rejected because chunk types already provide the needed
  inputs.

## Decision 5: Use OpenAI GPT only for bounded section summaries

**Decision**: Generate section summaries with OpenAI GPT through LangChain
OpenAI integration, using bounded prompts that include only the LDUs assigned to
one section and enforce a structured summary schema.

**Rationale**: Summaries are the one Stage 4 responsibility that benefits from
LLM synthesis. Keeping prompts bounded by configured chunk limits and validating
the returned structure preserves cost control and reduces hallucination risk.
During planning, LangChain documentation was consulted for structured-output
best practices, but runtime remains independent of MCP.

**Alternatives considered**:

- Rule-based summary generation: rejected because it produces poor navigation
  summaries for long mixed-content sections.
- Unstructured LLM responses: rejected because downstream indexing needs schema
  validation and formatting guarantees.

## Decision 6: Use ChromaDB for real local vector ingestion

**Decision**: Use ChromaDB as the Stage 4 local vector store and persist the
collection under a configurable path inside `.refinery/pageindex/`.

**Rationale**: ChromaDB gives durable local storage, simple metadata filtering,
and a lightweight integration path for section-first retrieval preparation. It
meets the explicit requirement for a real vector database without adding remote
infrastructure.

**Alternatives considered**:

- FAISS only: rejected because durable local metadata persistence is less direct
  for the requested workflow.
- Mock or in-memory vector layer: rejected because the user explicitly forbids
  mocks here.

## Decision 7: Provide section-first narrowing as a helper, not a query agent

**Decision**: Expose a lightweight section-ranking helper inside the Stage 4
indexing layer that accepts a topic string and ranks relevant sections before
full semantic search.

**Rationale**: The feature needs retrieval preparation but must stop short of
final query behavior. A helper scoped to section narrowing satisfies the use
case while respecting the Stage 4 boundary.

**Alternatives considered**:

- Implement the final retrieval/query agent: rejected because it is explicitly
  out of scope.
- Skip section ranking entirely: rejected because section-first narrowing is a
  stated critical use case.
