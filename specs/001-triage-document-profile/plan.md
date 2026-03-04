# Implementation Plan: Stage 1 Triage Agent (Document Classifier)

**Branch**: `001-triage-document-profile` | **Date**: 2026-03-04 | **Spec**: [spec.md](/c:/Abdu/synthesis-ai/specs/001-triage-document-profile/spec.md)
**Input**: Feature specification from `/specs/001-triage-document-profile/spec.md`

## Summary

Build Stage 1 of the Document Intelligence Refinery as the first LangGraph node that profiles each PDF into a deterministic, strictly typed `DocumentProfile`.  
The stage computes deterministic profiling metrics, logs auditable profiling entries to `.refinery/profiling_ledger.jsonl`, performs language detection with code+confidence, and routes extraction strategy via origin/layout/cost classification.

## Technical Context

**Language/Version**: Python >=3.14 (from `pyproject.toml`)  
**Primary Dependencies**: pydantic, pdfplumber, langgraph, pytest, lightweight language detection library (deterministic mode)  
**Storage**: `.refinery/profiles/{doc_id}.json` for profile artifacts and `.refinery/profiling_ledger.jsonl` for profiling observability logs  
**Testing**: pytest unit tests for origin detection, layout detection, domain classification, language detection, cost mapping, deterministic rerun equality, and serialization consistency  
**Target Platform**: Local and server-side Python runtime on Windows/Linux  
**Project Type**: Python library-style pipeline module with CLI-invokable entrypoint integration  
**Performance Goals**: Process a typical <=50-page PDF profile in <=5 seconds on standard developer hardware and keep profiling log emission non-blocking for successful runs  
**Constraints**: No LLM inference for `origin_type` and `layout_complexity`; deterministic output; structured typed outputs; Stage 1 only (no extraction implementation)  
**Scale/Scope**: Stage 1 triage for heterogeneous enterprise PDFs, with known-sample evaluation baseline and deterministic replay behavior

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase-0 Gate Assessment

- `Architecture`: PASS. Plan keeps strict modular boundaries with typed `DocumentProfile` and `GraphState` contracts.
- `Testing`: PASS. Plan includes unit coverage for classification, language detection, determinism, and serialization checks.
- `Provenance`: PASS (Stage-scoped). Stage 1 does not emit extracted answer units; provenance payload enforcement remains delegated to downstream extraction stages.
- `Escalation Guard`: PASS. Cost classification remains deterministic and fail-closed to higher-cost strategies when signals are weak/conflicting.
- `Performance/Cost`: PASS. Fast-text-first routing and deterministic cost mapping are preserved.
- `Observability`: PASS. Plan mandates `.refinery/profiling_ledger.jsonl` with doc-level metrics, classifications, and processing time.

### Post-Phase-1 Re-Check

- `Architecture`: PASS. Data model and contracts preserve typed boundaries and pluggable strategy interfaces.
- `Testing`: PASS. Design artifacts include deterministic repeat-run tests, known-sample classification checks, language tests, and serialization consistency tests.
- `Provenance`: PASS (Stage-scoped, unchanged).
- `Escalation Guard`: PASS. Cost resolver remains deterministic with explicit rule outcomes.
- `Performance/Cost`: PASS. Evaluation tasks verify deterministic routing outcomes on known samples.
- `Observability`: PASS. Profiling ledger contract includes required audit fields and deterministic metric traceability.

## Project Structure

### Documentation (this feature)

```text
specs/001-triage-document-profile/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- triage-node-contract.md
|   `-- document-profile.schema.json
`-- tasks.md
```

### Source Code (repository root)

```text
src/
|-- synthesis_ai/
|   |-- graph/
|   |   `-- triage_node.py
|   |-- models/
|   |   |-- document_profile.py
|   |   `-- graph_state.py
|   `-- triage/
|       |-- pdf_stats_analyzer.py
|       |-- origin_classifier.py
|       |-- layout_classifier.py
|       |-- extraction_cost_resolver.py
|       |-- profiling_logger.py
|       |-- language_detector.py
|       |-- profile_repository.py
|       `-- domain/
|           |-- strategy.py
|           `-- keyword_strategy.py

tests/
|-- unit/
|   |-- test_origin_classifier.py
|   |-- test_layout_classifier.py
|   |-- test_domain_classifier.py
|   |-- test_language_detector.py
|   |-- test_extraction_cost_resolver.py
|   |-- test_determinism.py
|   |-- test_known_samples_accuracy.py
|   `-- test_document_profile_serialization.py
`-- fixtures/
    `-- pdf_samples/
```

**Structure Decision**: Single Python project structure with explicit separation of models, triage components, and graph node orchestration to satisfy modularity, determinism, and observability principles.

## Complexity Tracking

No constitution violations requiring justification.
