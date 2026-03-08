# Phase 0 Research: Stage 2 Structure Extraction Layer

## Decision 1: Strategy A text extractor library
- Decision: Use `pdfplumber` as default `FastTextExtractor` backend; keep optional `pymupdf` adapter.
- Rationale: Reuses existing stack and deterministic parsing path.
- Alternatives considered:
  - `pymupdf` only: rejected due to migration risk.
  - OCR-first for all docs: rejected for cost/latency.

## Decision 2: Strategy B provider integration
- Decision: Implement adapter interface and configure Docling-first / MinerU-compatible provider path.
- Rationale: Swappable provider without router rewrite.
- Alternatives considered:
  - Hard-coded provider in router: rejected due to coupling.

## Decision 3: Vision multimodal method in LangGraph
- Decision: Use a LangGraph extraction node function that invokes a multimodal OpenRouter-backed chat model.
- Rationale: LangGraph docs support node functions with `state` and optional `config`, and model invocation inside node flow.
- Alternatives considered:
  - External ad-hoc call outside graph node: rejected due to observability/context propagation drift.

## Decision 4: Structured extraction prompts and output
- Decision: Use structured prompt templates and schema-constrained parsing (typed output contract).
- Rationale: Reduces parse ambiguity and normalizes extraction output.
- Alternatives considered:
  - Free-form parsing: rejected due to instability.

## Decision 5: Vision trigger policy
- Decision: Trigger VisionExtractor when `scanned_image`, low confidence after A/B, or handwriting detected.
- Rationale: Captures low OCR-quality and handwriting cases while containing cost.
- Alternatives considered:
  - Trigger only on scanned image: rejected due to low-confidence digital edge cases.

## Decision 6: Budget guard policy
- Decision: Enforce per-document token accounting, cost estimation, and configurable hard cap.
- Rationale: Meets constitution cost-control requirements.
- Alternatives considered:
  - Logging-only budget: rejected because cap must be enforced.

## Decision 7: Ledger traceability
- Decision: Write one JSONL ledger entry per strategy attempt with threshold rule reference.
- Rationale: Full escalation path auditability.
- Alternatives considered:
  - Final-attempt-only logging: rejected due to incomplete trace.

## Resolved Clarifications

All Stage 2 technical context items are resolved. No `NEEDS CLARIFICATION` remains.
