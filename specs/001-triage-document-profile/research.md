# Phase 0 Research: Stage 1 Triage Agent

## Decision 1: Origin classification heuristic thresholds are deterministic and page-aggregated
- Decision: Compute page-level character density and image-area ratio, then classify origin using fixed thresholds and aggregate rules:
  - `native_digital`: median character density >= 0.002 and median image ratio <= 0.20, with font metadata present on most pages.
  - `scanned_image`: median character density < 0.0002 and median image ratio >= 0.60.
  - `mixed`: mixed page groups where neither native nor scanned dominates >=80% of pages.
  - `form_fillable`: AcroForm fields detected regardless of other heuristics.
- Rationale: Fixed thresholding with deterministic precedence gives reproducible behavior and directly satisfies non-LLM requirement.
- Alternatives considered:
  - Adaptive thresholds by corpus statistics: rejected due to non-determinism across datasets.
  - ML classifier: rejected because this stage must remain deterministic and unit-testable.

## Decision 2: Layout complexity from geometric heuristics only
- Decision: Use x-coordinate clustering, whitespace gap analysis, and bounding-box alignment:
  - `multi_column`: >=2 persistent x-clusters across content bands.
  - `table_heavy`: repeated grid-like alignment patterns across rows/columns exceed threshold.
  - `figure_heavy`: page or document image ratio high while text block density low.
  - `single_column`: one dominant reading column with consistent left-aligned flow.
  - `mixed`: competing signals without clear winner.
- Rationale: Layout signals are available from PDF primitives and remain deterministic.
- Alternatives considered:
  - Computer vision layout model for all docs: rejected due to unnecessary cost in Stage 1.
  - Manual document tags: rejected because source PDFs are heterogeneous and often untagged.

## Decision 3: Domain hint via pluggable strategy interface
- Decision: Implement `DomainClassifierStrategy` interface and default `KeywordFrequencyDomainStrategy` with deterministic weighted lexicons for `financial|legal|technical|medical|general`.
- Rationale: Strategy interface allows future replacement (e.g., VLM classifier) without changing triage contract.
- Alternatives considered:
  - Hard-coded `if/else` in triage node: rejected due to poor extensibility.
  - LLM-only domain classification: rejected for determinism and testability constraints.

## Decision 4: Extraction cost mapping table is explicit and fail-closed
- Decision: `ExtractionCostResolver` maps `(origin_type, layout_complexity)` to cost class with conservative overrides:
  - scanned image or figure-heavy dominant -> `needs_vision_model`
  - multi-column/table-heavy/mixed layouts with readable text -> `needs_layout_model`
  - native + single-column with stable text signals -> `fast_text_sufficient`
- Rationale: Explicit mapping is auditable, deterministic, and enforces escalation guard.
- Alternatives considered:
  - Confidence-only numeric threshold map: rejected because it obscures routing logic.
  - Always layout/vision: rejected due to cost and latency.

## Decision 5: Persistence and observability contract for Stage 1
- Decision: Persist `DocumentProfile` to `.refinery/profiles/{doc_id}.json` and emit triage decision trace (input id, classifier outputs, selected cost class, duration, deterministic version) to ledger logging.
- Rationale: This supports auditability principle and reproducibility for downstream stages.
- Alternatives considered:
  - In-memory only profile: rejected because downstream stages require stable artifact.
  - Opaque logging without decision fields: rejected due to constitutional observability needs.

## Decision 6: LangGraph integration pattern
- Decision: Use triage as the first graph node with `GraphState` typed model containing `doc_id`, `file_path`, and optional `document_profile`; triage node populates `document_profile` and returns updated state.
- Rationale: Keeps stage order explicit and typed at graph boundary.
- Alternatives considered:
  - Side-channel profile file without graph state update: rejected due to weaker pipeline composability.
  - Untyped dictionary state: rejected by typed contract invariant.

## Resolved Clarifications

All technical-context unknowns are resolved in this document.
