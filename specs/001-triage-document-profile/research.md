# Phase 0 Research: Stage 1 Triage Agent (Challenge Layout)

## Decision 1: Deterministic language detection
- Decision: Use a lightweight language detection library with deterministic seed/config and return both language code and confidence.
- Rationale: Satisfies Stage 1 typed output and repeatability requirements.
- Alternatives considered:
  - Heavy multilingual models: rejected due to unnecessary Stage 1 complexity.
  - Language without confidence: rejected because confidence is required in profile contract.

## Decision 2: Constitution-aligned audit ledger naming
- Decision: Stage 1 writes triage audit events to `.refinery/extraction_ledger.jsonl`.
- Rationale: Aligns with constitution observability principle and avoids ledger-name drift.
- Alternatives considered:
  - Separate `profiling_ledger.jsonl`: rejected due to constitution mismatch and audit fragmentation.

## Decision 3: Rule externalization format
- Decision: Store triage thresholds, classifier rules, and deterministic controls in `rubric/extraction_rules.yaml`.
- Rationale: Keeps Stage 1 behavior configurable and auditable without code rewrites.
- Alternatives considered:
  - Hard-coded thresholds: rejected due to poor traceability/change control.

## Decision 4: Known-sample evaluation protocol
- Decision: Include deterministic repeat-run test and known-sample classification validation in unit test suite.
- Rationale: Directly validates success criteria and deterministic guarantees before Stage 2.
- Alternatives considered:
  - Manual ad hoc checks: rejected due to weak reproducibility.

## Decision 5: Strict stage boundary
- Decision: Exclude Stage 2 extraction artifacts/components from Stage 1 plan and contracts.
- Rationale: Prevents scope creep and preserves implementation focus on triage.
- Alternatives considered:
  - Partial Stage 2 placeholders in Stage 1 design: rejected as unnecessary coupling.

## Resolved Clarifications

All Stage 1 technical-context unknowns are resolved.
