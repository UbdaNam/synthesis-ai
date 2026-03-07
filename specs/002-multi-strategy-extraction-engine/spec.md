# Feature Specification: Structure Extraction Layer

**Feature Branch**: `002-multi-strategy-extraction-engine`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Build Stage 2 of the document intelligence pipeline: the Structure Extraction Layer..."

## User Scenarios & Testing _(mandatory)_

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Route And Extract Structured Content (Priority: P1)

As a downstream pipeline consumer, I need each document to be extracted into a normalized structured format using the most suitable strategy so later stages receive usable, consistent content.

**Why this priority**: This is the core business value of Stage 2; without reliable structured extraction, later stages cannot operate correctly.

**Independent Test**: Can be fully tested by providing representative simple, complex, and mixed-origin documents with a Stage 1 profile, then verifying the produced output is a valid structured ExtractedDocument with preserved document structure.

**Acceptance Scenarios**:

1. **Given** a document with a profile indicating simple native digital content, **When** Stage 2 runs, **Then** it uses Fast Text extraction and returns a normalized ExtractedDocument.
2. **Given** a document with a profile indicating complex layout or mixed origin, **When** Stage 2 runs, **Then** it uses Layout-aware extraction and returns structured output preserving sections, tables, and reading order.
3. **Given** a document with a profile indicating scanned or low-confidence risk, **When** Stage 2 runs, **Then** it uses Vision-augmented extraction and returns structured output with provenance metadata.

---

### User Story 2 - Enforce Escalation Guard (Priority: P2)

As a quality owner, I need low-confidence extraction to be automatically retried with a stronger strategy so poor results are blocked from reaching downstream stages.

**Why this priority**: The mandatory escalation guard prevents silent quality failures and is a non-negotiable reliability control.

**Independent Test**: Can be tested by forcing low confidence on lower-cost strategies and verifying automatic escalation occurs until confidence threshold is met or processing fails closed.

**Acceptance Scenarios**:

1. **Given** Fast Text extraction returns low confidence, **When** confidence is evaluated, **Then** the system retries with Layout-aware extraction automatically.
2. **Given** Layout-aware extraction also returns low confidence, **When** confidence is evaluated, **Then** the system retries with Vision-augmented extraction automatically.
3. **Given** Vision-augmented extraction remains below acceptance threshold, **When** no stronger strategy is available, **Then** the system rejects the result and marks the document for manual or downstream exception handling.

---

### User Story 3 - Provide Decision And Cost Auditability (Priority: P3)

As an operations analyst, I need a clear audit trail of strategy choice, confidence outcomes, escalation path, and cost so I can monitor quality, explain decisions, and optimize processing spend.

**Why this priority**: Observability and cost tracking are required for governance and continuous tuning, but they depend on core extraction behavior.

**Independent Test**: Can be tested by processing a batch of documents and verifying each run records strategy decisions, confidence values, escalation steps, and cost metrics linked to the output.

**Acceptance Scenarios**:

1. **Given** any processed document, **When** Stage 2 completes, **Then** an audit record shows initial strategy selection rationale and all retry decisions.
2. **Given** a document that escalated strategies, **When** the audit trail is reviewed, **Then** it includes confidence scores and per-attempt cost with final disposition.

---

### Edge Cases

- DocumentProfile is missing required classification fields or has contradictory indicators (for example, both "native digital" and "scanned-only").
- A document contains mixed page types where some pages are high quality text and others are low-quality scans.
- Confidence is exactly on the threshold boundary.
- Extraction output is structurally incomplete (for example, missing page-level content) even when confidence appears high.
- Vision-augmented extraction exceeds configured cost budget before producing acceptable confidence.
- All strategies fail due to unreadable or corrupted input; the pipeline must fail closed with explicit reason.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST accept a Stage 1 DocumentProfile as required input for extraction strategy selection.
- **FR-002**: System MUST support exactly three extraction strategies in this stage: Fast Text, Layout-aware, and Vision-augmented.
- **FR-003**: System MUST select an initial extraction strategy using DocumentProfile signals and documented routing rules.
- **FR-004**: System MUST produce a normalized ExtractedDocument output format for all accepted extraction results, regardless of strategy used.
- **FR-005**: System MUST preserve document structure in the output, including page boundaries, reading order, and structural elements such as headings, paragraphs, tables, and lists when present.
- **FR-006**: System MUST compute an extraction confidence result for every extraction attempt before accepting output.
- **FR-007**: System MUST reject any extraction attempt that does not meet the configured confidence acceptance threshold.
- **FR-008**: System MUST enforce mandatory escalation guard behavior: when a lower-cost strategy fails confidence acceptance, it automatically retries with the next stronger strategy.
- **FR-009**: System MUST continue escalation until output meets confidence acceptance or no stronger strategy remains.
- **FR-010**: System MUST fail closed and prevent downstream handoff when all available strategies fail confidence acceptance.
- **FR-011**: System MUST record an auditable decision trace for each document, including selected strategy, confidence outcomes, escalation sequence, and final disposition.
- **FR-012**: System MUST record per-document extraction cost and strategy-level cost contribution for operational review.
- **FR-013**: System MUST expose clear failure reasons for documents rejected due to low confidence, invalid input profile, unreadable content, or budget constraints.
- **FR-014**: System MUST ensure output includes sufficient provenance metadata to trace extracted segments back to original document locations.

## Constitution Alignment _(mandatory)_

### Non-Negotiable Invariants

- **CI-001 Typed Contracts**: Identify all inter-stage payloads and corresponding
  typed models (no untyped dictionaries). Stage 2 input is `DocumentProfile`; primary output is `ExtractedDocument`; internal attempt records are typed and versioned.
- **CI-002 Provenance**: Define how `page_number`, `bounding_box`, and `content_hash`
  are produced and validated. Every extracted structural segment carries source page number, source region, and stable content hash; records missing provenance are invalid and rejected.
- **CI-003 Escalation Guard**: Define confidence threshold(s), routing behavior, and
  fail-closed conditions. Confidence threshold is applied per attempt; low-confidence attempts trigger automatic escalation to next stronger strategy; if highest strategy is still below threshold, processing fails closed.
- **CI-004 Deterministic Chunking**: Define chunking rules and determinism guarantees.
  Chunk boundaries are derived from structural units and stable ordering rules so repeated runs on identical inputs produce the same chunk sequence and identifiers.
- **CI-005 Cost Controls**: Define fast-text-first policy and per-document vision
  extraction budget. Strategy escalation always starts from the lowest-cost valid option and respects a configurable per-document ceiling for strongest-strategy usage.
- **CI-006 Observability**: Define fields logged to `extraction_ledger.jsonl`,
  including strategy decision trace and processing times. Each entry includes document identifier, profile summary, selected strategy, attempt-level confidence, escalation path, attempt timing, cost, and final status.

### Key Entities _(include if feature involves data)_

- **DocumentProfile**: Stage 1 document characterization used to route extraction strategy; includes source type signals, complexity indicators, and quality hints.
- **StrategyDecision**: Strategy selection and escalation decision record; includes chosen strategy, decision rationale, decision order, and timestamp.
- **ExtractionAttempt**: One execution of a strategy for a document; includes attempt number, strategy used, confidence result, processing duration, and attempt cost.
- **ExtractedDocument**: Normalized structured document output accepted for downstream stages; includes structural sections, ordered content blocks, and provenance metadata.
- **ExtractionSegment**: Atomic extracted content unit (for example heading, paragraph, table cell, list item) with position/order metadata and confidence attributes.
- **ExtractionOutcome**: Final status object indicating accepted output or fail-closed rejection with explicit reason.

## Assumptions

- Stage 1 always provides a valid `DocumentProfile` for documents entering Stage 2; invalid profiles are treated as explicit input errors.
- Confidence scoring is available and comparable across strategies so one acceptance threshold policy can govern pass/retry/reject decisions.
- A stronger strategy is defined as one that is expected to improve extraction quality at higher processing cost.
- Later stages require stable structure and provenance to support deterministic processing and audit requirements.

## Dependencies

- Availability of Stage 1 `DocumentProfile` for every document submitted to Stage 2.
- Availability of strategy execution services for Fast Text, Layout-aware, and Vision-augmented extraction.
- Availability of audit log storage for strategy traces, confidence history, timing, and cost records.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: At least 95% of documents with valid profiles produce an accepted ExtractedDocument without manual intervention.
- **SC-002**: 100% of extraction attempts below the confidence threshold are prevented from downstream handoff unless successfully escalated and revalidated.
- **SC-003**: At least 98% of accepted ExtractedDocuments preserve correct page order and structural hierarchy as verified by quality review sampling.
- **SC-004**: 100% of processed documents produce an audit record containing strategy decisions, confidence outcomes, and cost traceability.
- **SC-005**: For documents initially routed to lower-cost strategies that fail confidence, at least 99% automatically escalate to a stronger strategy within the same processing run.
