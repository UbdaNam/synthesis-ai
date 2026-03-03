<!--
Sync Impact Report
- Version change: template (unversioned) -> 1.0.0
- Modified principles:
  - Template Principle 1 -> I. Modular Architecture and Typed Contracts (NON-NEGOTIABLE)
  - Template Principle 2 -> II. Test Discipline and Deterministic Processing (NON-NEGOTIABLE)
  - Template Principle 3 -> III. Provenance and Data Integrity Guarantees (NON-NEGOTIABLE)
  - Template Principle 4 -> IV. Performance and Cost-Aware Escalation (NON-NEGOTIABLE)
  - Template Principle 5 -> V. Configuration-Driven Extensibility
  - Added principle -> VI. Auditability and Operational Observability (NON-NEGOTIABLE)
- Added sections:
  - Non-Negotiable Invariants and Violation Handling
  - Delivery Workflow and Quality Gates
- Removed sections:
  - None
- Templates requiring updates:
  - .specify/templates/plan-template.md: updated
  - .specify/templates/spec-template.md: updated
  - .specify/templates/tasks-template.md: updated
  - .specify/templates/commands/*.md: pending (directory not present)
  - README.md: reviewed, no principle-reference changes required
  - docs/quickstart.md: reviewed, file not present
  - .codex/AGENTS.md: reviewed, no principle-reference changes required
- Follow-up TODOs:
  - TODO(COMMAND_TEMPLATES): create `.specify/templates/commands/` or confirm intentionally omitted.
-->
# The Document Intelligence Refinery Constitution

## Core Principles

### I. Modular Architecture and Typed Contracts (NON-NEGOTIABLE)
All pipeline stages MUST enforce strict modular boundaries. The extraction layer MUST
use a Strategy pattern, and agent orchestration logic MUST remain separate from
extraction strategy implementations. Domain payloads exchanged between stages MUST use
typed Pydantic models. Untyped dictionaries are prohibited at stage boundaries.
Rationale: strong contracts prevent hidden coupling and reduce silent runtime failures.

### II. Test Discipline and Deterministic Processing (NON-NEGOTIABLE)
The codebase MUST include unit tests for document classification, confidence scoring,
and escalation routing. It MUST include validation tests for chunking invariants and
regression tests for known extraction failures. Chunking behavior MUST be deterministic
for identical inputs and configuration.
Rationale: determinism and regression protection are required for production stability.

### III. Provenance and Data Integrity Guarantees (NON-NEGOTIABLE)
Every extracted unit MUST include `page_number` and `bounding_box`. Every LDU MUST
include `content_hash`. The system MUST NOT return answers without provenance metadata.
An escalation guard MUST block low-confidence outputs from downstream consumption.
Rationale: traceable evidence is required for trustworthy document intelligence.

### IV. Performance and Cost-Aware Escalation (NON-NEGOTIABLE)
Fast text extraction MUST be attempted first. Automatic escalation MUST occur only when
confidence is below configured thresholds. Vision extraction MUST enforce a
per-document cost budget. Strategy usage and cost MUST be recorded in a ledger.
Rationale: predictable latency and spend control are core production constraints.

### V. Configuration-Driven Extensibility
New extraction strategies MUST be onboarded through configuration (YAML) rather than
hard-coded rewrites. New document types MUST be introduced by configuration updates.
Vector store and fact table integrations MUST be pluggable through stable interfaces.
Rationale: extensibility must not require risky structural rewrites.

### VI. Auditability and Operational Observability (NON-NEGOTIABLE)
All extraction attempts MUST be logged to `extraction_ledger.jsonl` with strategy,
confidence, routing decision, and estimated cost fields. Processing duration MUST be
recorded per document and per strategy attempt. Strategy decisions MUST be auditable
from logs without requiring source-code inspection.
Rationale: production operations require forensic-quality audit trails.

## Non-Negotiable Invariants and Violation Handling

- Invariants labeled NON-NEGOTIABLE are release-blocking.
- Any pull request that violates a non-negotiable invariant MUST be rejected until fixed.
- Runtime detection of a non-negotiable violation MUST fail closed: no downstream answer
  emission, explicit error event, and ledger entry with violation code.
- Escalation-guard violations MUST trigger immediate halt of downstream publication for
  the affected document.
- Temporary exceptions require written waiver approval by two maintainers, a scope limit,
  an expiry date, and linked remediation tasks.

## Delivery Workflow and Quality Gates

- Plan-phase Constitution Check MUST map each principle to concrete implementation tasks
  and test evidence before coding starts.
- Spec documents MUST define provenance fields, confidence thresholds, escalation policy,
  deterministic chunking expectations, and budget constraints.
- Task plans MUST include explicit work items for typed models, strategy interfaces,
  provenance enforcement, ledger logging, and mandatory test suites.
- Merge criteria require passing unit, validation, and regression tests plus review
  confirmation that no untyped inter-stage payloads remain.

## Governance

This constitution overrides conflicting local conventions for architecture, testing,
and release criteria in The Document Intelligence Refinery.

Amendment process:
- Propose changes via pull request that includes rationale, migration impact, and update
  notes for affected templates and guides.
- Approval requires at least two maintainers.
- Ratified amendments MUST include a semantic version bump justification.

Versioning policy:
- MAJOR: incompatible governance changes, principle removals, or redefinition of
  non-negotiable guarantees.
- MINOR: new principle or materially expanded mandatory guidance.
- PATCH: clarifications, wording improvements, typo fixes, and non-semantic edits.

Compliance review expectations:
- Every feature plan and pull request MUST include an explicit constitution compliance
  check.
- Quarterly audits MUST sample merged changes for adherence to typed contracts,
  provenance guarantees, escalation controls, and ledger completeness.

**Version**: 1.0.0 | **Ratified**: 2026-03-03 | **Last Amended**: 2026-03-03

