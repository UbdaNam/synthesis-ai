# Feature Specification: Triage Agent Document Profiling

**Feature Branch**: `001-triage-document-profile`  
**Created**: 2026-03-04  
**Status**: Draft  
**Input**: User description: "triage agent - Build Stage 1 of a LangGraph-based document intelligence system: the Triage Agent (Document Classifier). This stage must analyze a PDF and produce a strictly typed DocumentProfile (Pydantic model) that governs downstream extraction strategy selection. The DocumentProfile must include the following classification dimensions: Origin Type: native_digital | scanned_image | mixed | form_fillable Layout Complexity: single_column | multi_column | table_heavy | figure_heavy | mixed Language: detected language code + confidence Domain Hint: financial | legal | technical | medical | general Estimated Extraction Cost: fast_text_sufficient | needs_layout_model | needs_vision_model Implementation constraints: - Use pdfplumber to compute: - character density - image-to-page area ratio - font metadata presence - Use whitespace and bounding box heuristics for layout classification. - Implement domain_hint using a pluggable strategy pattern. - Do NOT use LLM for origin_type or layout detection. - Produce a Pydantic DocumentProfile. - Persist the profile to `.refinery/profiles/{doc_id}.json`. - This node must integrate as the first node in a LangGraph graph. The output must be deterministic and unit-testable."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route Extraction by Document Type (Priority: P1)

As a pipeline operator, I need each incoming PDF profiled into a strict document classification so the system can choose the right extraction strategy before costly processing begins.

**Why this priority**: Strategy routing is the core business value of triage; without it, downstream stages cannot make consistent extraction decisions.

**Independent Test**: Submit representative PDFs (native digital, scanned, mixed, and form-fillable) and verify each receives a valid profile and a corresponding extraction-cost class.

**Acceptance Scenarios**:

1. **Given** a text-native PDF, **When** triage runs, **Then** the profile marks origin type as `native_digital` and cost as `fast_text_sufficient`.
2. **Given** a scan-only PDF, **When** triage runs, **Then** the profile marks origin type as `scanned_image` and cost as `needs_vision_model`.
3. **Given** a mixed PDF with text and scanned pages, **When** triage runs, **Then** the profile marks origin type as `mixed` and assigns a non-fast path cost class.

---

### User Story 2 - Preserve Deterministic Typed Output (Priority: P2)

As a platform engineer, I need triage output to be strictly typed, persisted, and repeatable so that downstream nodes and tests can rely on stable behavior.

**Why this priority**: Deterministic, typed output reduces operational incidents and enables reliable automation and regression testing.

**Independent Test**: Run triage twice on the same PDF and verify both persisted profiles are schema-valid and identical.

**Acceptance Scenarios**:

1. **Given** any valid PDF and document identifier, **When** triage completes, **Then** a schema-valid profile is persisted at `.refinery/profiles/{doc_id}.json`.
2. **Given** the same PDF and inputs, **When** triage is executed repeatedly, **Then** all profile fields remain identical.

---

### User Story 3 - Support Domain-Aware Routing Policies (Priority: P3)

As a product owner, I need each profile to include a domain hint so future extraction policies can adapt to financial, legal, technical, medical, or general documents.

**Why this priority**: Domain hinting is important for policy quality, but extraction can still run without advanced domain-specific behavior in initial rollout.

**Independent Test**: Evaluate curated domain documents and verify the output domain hint is always one allowed class and produced through a replaceable strategy component.

**Acceptance Scenarios**:

1. **Given** domain-representative PDFs, **When** triage runs, **Then** each profile includes one allowed domain hint value.
2. **Given** an alternate domain strategy implementation, **When** triage is configured to use it, **Then** profile generation still succeeds without changing the profile contract.

### Edge Cases

- PDF contains no extractable characters and no detectable image blocks; system still returns a valid profile using conservative defaults and flags higher extraction cost.
- PDF pages have inconsistent structures (for example, text-heavy pages and figure-heavy pages mixed); layout complexity resolves to `mixed`.
- PDF metadata is missing or malformed; profiling continues using observable page content only.
- Unsupported or low-confidence language detection; profile still includes a language code and confidence with a conservative fallback confidence value.
- `doc_id` collision on persistence path; existing profile file is deterministically replaced for idempotent reruns.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST profile each input PDF into a strict `DocumentProfile` contract before any downstream extraction stage runs.
- **FR-002**: System MUST classify `origin_type` as one of: `native_digital`, `scanned_image`, `mixed`, `form_fillable`.
- **FR-003**: System MUST classify `layout_complexity` as one of: `single_column`, `multi_column`, `table_heavy`, `figure_heavy`, `mixed`.
- **FR-004**: System MUST populate language with both a detected language code and confidence score.
- **FR-005**: System MUST classify `domain_hint` as one of: `financial`, `legal`, `technical`, `medical`, `general`.
- **FR-006**: System MUST classify `estimated_extraction_cost` as one of: `fast_text_sufficient`, `needs_layout_model`, `needs_vision_model`.
- **FR-007**: System MUST derive origin and layout classifications using deterministic document-inspection heuristics and MUST NOT depend on generative AI inference for those fields.
- **FR-008**: System MUST use page-level measurable signals including character density, image-to-page area ratio, and font metadata presence for origin and cost decisions.
- **FR-009**: System MUST use whitespace and bounding-region distribution heuristics to determine layout complexity.
- **FR-010**: System MUST make domain classification through a pluggable strategy component that can be replaced without changing `DocumentProfile`.
- **FR-011**: System MUST persist one profile per document at `.refinery/profiles/{doc_id}.json`.
- **FR-012**: System MUST run this triage stage as the first node in the document-intelligence graph workflow.
- **FR-013**: System MUST produce deterministic output for identical inputs and configuration.
- **FR-014**: System MUST expose behavior that can be verified via unit tests for each classification dimension and persistence outcome.

## Constitution Alignment *(mandatory)*

### Non-Negotiable Invariants

- **CI-001 Typed Contracts**: `DocumentProfile` is the inter-stage payload emitted by triage, and all downstream routing decisions consume this typed profile rather than untyped maps.
- **CI-002 Provenance**: Triage outputs document-level classification and confidence traces. Page-level provenance fields (`page_number`, `bounding_box`, `content_hash`) are not emitted by this stage and are explicitly delegated to extraction stages that generate extractable artifacts.
- **CI-003 Escalation Guard**: If profiling confidence is low or source signals conflict, triage routes to a higher-cost extraction class (`needs_layout_model` or `needs_vision_model`) rather than the fast path.
- **CI-004 Deterministic Chunking**: This stage performs no chunking. Determinism is guaranteed through fixed heuristics, fixed thresholding rules, and stable ordering of page analysis.
- **CI-005 Cost Controls**: Triage enforces fast-text-first selection only when document signals support it; otherwise it assigns higher-cost classes conservatively to avoid failed extraction passes.
- **CI-006 Observability**: Triage logs profile decisions, confidence scores, selected extraction cost class, and processing duration so routing behavior is auditable.

### Key Entities *(include if feature involves data)*

- **DocumentProfile**: Strict classification record for one document with fields for origin type, layout complexity, language (code and confidence), domain hint, and estimated extraction cost.
- **LanguageSignal**: Detected language code and confidence pair used inside the profile for downstream decisioning and auditing.
- **DomainHintStrategy**: Swappable classification policy component that maps document evidence to one allowed domain hint.
- **ProfileArtifact**: Persisted JSON representation of the profile stored by `doc_id` for reproducible downstream use.

## Assumptions

- Input is a valid PDF file accessible to the triage stage at runtime.
- The first stage in the graph is responsible only for classification and routing, not extraction of final business fields.
- When ambiguity exists in origin or layout signals, conservative routing to a more capable extraction class is preferred over under-classification.
- Domain hinting defaults to `general` when evidence is insufficient for a specialized class.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of processed PDFs produce a schema-valid `DocumentProfile` artifact with all required fields populated.
- **SC-002**: On a labeled evaluation set of at least 100 PDFs, origin-type classification agreement with expected labels is at least 90%.
- **SC-003**: On the same input set and unchanged configuration, repeated triage runs produce identical profile outputs in 100% of cases.
- **SC-004**: At least 95% of documents that require advanced processing are routed away from the fast text-only path, reducing failed downstream extraction attempts.
