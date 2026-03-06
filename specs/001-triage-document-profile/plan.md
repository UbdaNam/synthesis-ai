# Implementation Plan: Stage 1 Triage Agent (Clarified Scope)

**Branch**: `001-triage-document-profile` | **Date**: 2026-03-06 | **Spec**: [spec.md](/c:/Abdu/synthesis-ai/specs/001-triage-document-profile/spec.md)
**Input**: Feature specification from `/specs/001-triage-document-profile/spec.md`

## Summary

Implement Stage 1 only (Triage Agent & Document Profiling) as the first LangGraph node. Stage 1 computes deterministic PDF profiling signals, classifies `DocumentProfile`, persists `.refinery/profiles/{doc_id}.json`, and writes Stage-1 profiling/audit evidence to `.refinery/profiling_ledger.jsonl`.

LangGraph assembly is owned by `src/graph/`, while triage logic remains in `src/agents/triage.py`. `main.py` executes the compiled graph.

This plan explicitly excludes all Stage 2 extraction behavior.

## Technical Context

**Language/Version**: Python >=3.14  
**Primary Dependencies**: pydantic, pdfplumber, langdetect, langgraph, pytest  
**Storage**: `.refinery/profiles/{doc_id}.json` and `.refinery/profiling_ledger.jsonl`  
**Testing**: Deterministic unit tests + known-sample validation tests in `tests/`  
**Target Platform**: Local/server Python runtime (Windows/Linux)  
**Project Type**: Stage-1 triage classifier node for LangGraph  
**Performance Goals**: Per-document profiling with recorded `processing_time`  
**Constraints**: Deterministic outputs for identical input/config; no LLM for origin/layout detection; Stage 1 only (no extraction stage behavior)  
**Scale/Scope**: Triage-only profiling and routing signals for downstream Stage 2 handoff

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Pre-Phase-0 Gate Assessment

- `Architecture`: PASS. Typed payload boundary uses `GraphState` and `DocumentProfile`; graph assembly is isolated in `src/graph`.
- `Testing/Determinism`: PASS. Plan includes repeat-run equality tests and known-sample classification tests.
- `Provenance/Stage Boundary`: PASS. Stage 1 emits profiling/classification evidence only and defers extraction provenance artifacts to Stage 2.
- `Escalation Guard`: PASS. Cost class is deterministic and conservative under ambiguous/conflicting signals.
- `Performance/Cost`: PASS. Fast path is selected only when document signals justify `fast_text_sufficient`.
- `Observability`: PASS. Stage 1 logs profiling/classification evidence to `.refinery/profiling_ledger.jsonl` for audit/debug.

### Post-Phase-1 Re-Check

- `Architecture`: PASS. Graph entrypoint contract is explicit (`GraphState -> GraphState`) and Stage 1 remains isolated.
- `Testing/Determinism`: PASS. Design requires deterministic language detection and serialized output equality checks.
- `Provenance/Stage Boundary`: PASS. No extraction routing/execution components are introduced.
- `Escalation Guard`: PASS. Threshold/rule-based cost selection remains deterministic and auditable.
- `Performance/Cost`: PASS. Advanced-processing routing interpretation is explicitly defined.
- `Observability`: PASS. Evidence logging fields are specified and testable for completeness.

## Project Structure

### Documentation (this feature)

```text
specs/001-triage-document-profile/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- triage-node-contract.md
`-- tasks.md
```

### Required Challenge Structure

```text
src/
|-- models/
|   |-- document_profile.py
|   `-- graph_state.py
|-- graph/
|   |-- __init__.py
|   `-- graph.py
`-- agents/
    `-- triage.py

rubric/
`-- extraction_rules.yaml

.refinery/
|-- profiles/
`-- profiling_ledger.jsonl

tests/
`-- ... unit and validation tests for Stage 1 triage logic
```

**Structure Decision**: Stage 1 challenge layout is strict for this feature and intentionally excludes Stage 2 components.

## Core Components

1. `DocumentProfile` Pydantic model in `src/models/document_profile.py`.
2. `GraphState` Pydantic model in `src/models/graph_state.py`.
3. Stage 1 triage orchestrator in `src/agents/triage.py` that:
   - computes PDF signals (`character_density`, `image_ratio`, `font_metadata_presence`, layout signals),
   - classifies origin/layout/language/domain/cost deterministically,
   - persists profile output,
   - writes profiling evidence log entries.
4. Stage 1 graph assembly in `src/graph/graph.py` that:
   - builds `StateGraph(GraphState)`,
   - sets `triage` as entrypoint and finish point,
   - compiles the runtime graph used by `main.py`.
5. Externalized thresholds/rules in `rubric/extraction_rules.yaml`.

### Graph Entrypoint Contract (Stage 1 First Node)

- **Input Type**: `GraphState` with required fields:
  - `doc_id: str`
  - `file_path: str`
  - `document_profile: Optional[DocumentProfile] = None`
- **Graph Build API**: `build_graph(agent: TriageAgent | None = None) -> CompiledStateGraph`.
- **Entrypoint Name**: `triage`.
- **Node Role**: First node in LangGraph flow; consumes `doc_id` + `file_path`, computes and sets `document_profile`.
- **Output Type**: `GraphState` with identical identity fields and populated `document_profile`.
- **Contract Rule**: Downstream nodes MUST NOT execute before this node emits a schema-valid `DocumentProfile`.
- **Stage Scope**: Downstream nodes are intentionally out of scope for Stage 1; finish point remains `triage`.

### Stage 1 Decision Evidence Requirements

For every profiled document, Stage 1 MUST record the following minimum evidence fields:

- `doc_id`
- `character_density`
- `image_ratio`
- `font_metadata_presence`
- `layout_signals_used`
- `origin_type`
- `layout_complexity`
- `language_code`
- `language_confidence`
- `domain_hint`
- `estimated_extraction_cost`
- `processing_time`
- `threshold_rule_reference`

Measurable checks:

- **Reproducibility**: Repeated runs with identical input and configuration produce identical `DocumentProfile` payloads.
- **Explainability**: Every final classification output is traceable to logged signals and `threshold_rule_reference`.

### Deterministic Language Detection Default

- Default library: `langdetect`.
- Determinism requirement: seed detector once at process start using `DetectorFactory.seed = 0`.
- Required tests: English and non-English samples with deterministic language code/confidence outputs across repeated runs.

## Success-Evidence Mapping

- `SC-001` coverage: Schema-valid persisted `DocumentProfile` artifacts.
- `SC-002` coverage: Known-sample origin classification accuracy validation.
- `SC-003` coverage: Repeat-run deterministic equality checks.
- Graph build validation: graph contract test verifies compilation from `src/graph/graph.py`.
- Entrypoint validation: graph entrypoint test verifies `triage` execution and `GraphState.document_profile` output.
- Runtime validation: `main.py` invokes compiled graph using `GraphState` and prints profile payload.
- `SC-004` interpretation: “Documents requiring advanced processing” means documents where:
  - `estimated_extraction_cost == needs_layout_model`, or
  - `estimated_extraction_cost == needs_vision_model`.

All plan metrics referencing advanced-processing routing MUST use this definition.

## Stage Boundary Note

Stage 1 ends at deterministic document profiling, profile persistence, and profiling evidence logging.

- Stage 1 logs **profiling/classification evidence** to `.refinery/profiling_ledger.jsonl`.
- This is **not** Stage-2 extraction-attempt ledger work.
- Stage 1 does not implement extraction routing/execution components, extraction strategies, or extraction payload models.

## Assumptions and Defaults

- Stage 1 profiling logging is distinct from Stage 2 extraction-attempt ledgering.
- `langdetect` is acceptable as the default deterministic language detection library for this feature.
- Rule/threshold traceability is represented via stable `threshold_rule_reference` values sourced from `rubric/extraction_rules.yaml`.
- No Stage 2 architecture changes are introduced by this plan.
- Python imports are normalized around repository-root `src.*` paths to prevent runtime path drift.

## Complexity Tracking

No constitution violations requiring justification.
