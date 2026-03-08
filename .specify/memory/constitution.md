<!--
Sync Impact Report
- Version change: N/A (empty) -> 1.0.0
- Modified principles:
  - N/A -> I. Typed Contracts
  - N/A -> II. Determinism First
  - N/A -> III. Auditability and Provenance
  - N/A -> IV. Cost and Risk Control
  - N/A -> V. Validation and Testing
  - N/A -> VI. Separation of Concerns
  - N/A -> VII. Operability and Extensibility
- Added sections:
  - Operational Requirements
  - Delivery Workflow and Quality Gates
  - Governance
- Removed sections:
  - None
- Templates requiring updates:
  - [updated] .specify/templates/plan-template.md
  - [updated] .specify/templates/spec-template.md
  - [updated] .specify/templates/tasks-template.md
  - [pending: path missing] .specify/templates/commands/*.md
  - [updated] README.md
- Deferred TODOs:
  - None
-->

# Synthesis AI Engineering Constitution

## Core Principles

### I. Typed Contracts

- Every stage boundary MUST use explicit Pydantic schemas.
- Raw provider payloads MUST be normalized before crossing stage boundaries.
- Invalid stage outputs MUST fail closed and surface structured errors.
  Rationale: typed contracts prevent schema drift and silent corruption.

### II. Determinism First

- Deterministic logic MUST be used when measurable signals can solve the task.
- Routing and escalation decisions MUST be implemented outside the LLM unless a
  stage explicitly requires model reasoning.
- Given identical input, rules, and dependencies, routing outcomes MUST be
  reproducible where practical.
  Rationale: deterministic control reduces variance and operational risk.

### III. Auditability and Provenance

- Every stage MUST emit auditable artifacts or structured logs.
- Downstream answers MUST be traceable to source location metadata.
- Rule versions and threshold references MUST be persisted for each decision.
  Rationale: traceability is required for debugging, compliance, and trust.

### IV. Cost and Risk Control

- Expensive model usage MUST be budget-aware and explicitly bounded.
- Escalation to more expensive strategies MUST be rule-driven and observable.
- Low-confidence outputs MUST NOT pass silently downstream.
  Rationale: uncontrolled escalation causes avoidable cost and quality failures.

### V. Validation and Testing

- Every stage MUST have unit-testable core logic.
- Constitution invariants MUST be enforced by validation and tests, not only by
  convention.
- Repeated runs with the same configuration SHOULD be reproducible; exceptions
  MUST be documented.
  Rationale: governance without enforceable tests is not reliable governance.

### VI. Separation of Concerns

- Agents MUST orchestrate flow and state transitions.
- Strategies MUST perform bounded extraction work behind stable interfaces.
- Models MUST define contracts and validation rules.
- Transformation and validation logic MUST remain modular and independently
  testable.
  Rationale: modular boundaries enable safe iteration and lower coupling risk.

### VII. Operability and Extensibility

- The system MUST be inspectable through persisted artifacts, structured logs,
  and explicit stage boundaries.
- New document types SHOULD be onboarded through configuration and adapters
  before architectural rewrites are considered.
- Operational failure modes MUST return actionable error categories.
  Rationale: production systems must be operable and evolve without rework loops.

## Operational Requirements

- Stage outputs MUST include provenance fields (`page_number`, `bounding_box`,
  `content_hash`) where applicable.
- Extraction routing MUST support explicit confidence thresholds and fail-closed
  behavior.
- Ledger artifacts MUST record strategy, confidence, cost estimate, timing,
  escalation, and rule references.
- Configuration values affecting routing, thresholds, and budgets MUST be
  externalized and versioned.

## Delivery Workflow and Quality Gates

- Plan artifacts MUST include a constitution check before research and after
  design.
- Specs MUST define non-negotiable invariants for typed contracts, provenance,
  escalation guard, determinism, cost control, and observability.
- Tasks MUST include validation and regression coverage for governed behavior.
- Pull requests MUST demonstrate compliance through test evidence and artifact
  traces.

## Governance

- This constitution supersedes conflicting local conventions for this repository.
- Amendments MUST include: rationale, impact analysis, migration steps, and a
  semantic version bump decision.
- Versioning policy:
  - MAJOR: incompatible governance changes or principle removals/redefinitions.
  - MINOR: new principle/section or materially expanded mandatory guidance.
  - PATCH: clarifications and wording refinements without semantic change.
- Compliance review expectations:
  - Every feature plan MUST pass constitution gates before implementation.
  - Every implementation PR MUST show tests and artifacts proving compliance.
  - Violations MUST be resolved or explicitly waived with documented approval.

**Version**: 1.0.0 | **Ratified**: 2026-03-07 | **Last Amended**: 2026-03-07
