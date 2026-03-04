# Implementation Plan: Stage 1 Triage Agent (Document Classifier)

**Branch**: `001-triage-document-profile` | **Date**: 2026-03-04 | **Spec**: [spec.md](/c:/Abdu/synthesis-ai/specs/001-triage-document-profile/spec.md)
**Input**: Feature specification from `/specs/001-triage-document-profile/spec.md`

## Summary

Build Stage 1 of the Document Intelligence Refinery as the first LangGraph node that profiles each PDF into a deterministic, strictly typed `DocumentProfile`.  
The design uses modular classifiers (`PDFStatsAnalyzer`, `OriginClassifier`, `LayoutClassifier`, `DomainClassifierStrategy`, `ExtractionCostResolver`), persists profiles to `.refinery/profiles/{doc_id}.json`, and avoids LLM-based origin/layout decisions.

## Technical Context

**Language/Version**: Python >=3.14 (from `pyproject.toml`)  
**Primary Dependencies**: pydantic, pdfplumber, langgraph (graph orchestration), standard-library JSON/path utilities  
**Storage**: File-based JSON artifacts under `.refinery/profiles/` and ledger files under `.refinery/`  
**Testing**: pytest unit tests for origin detection, layout detection, cost mapping, and serialization determinism  
**Target Platform**: Local and server-side Python runtime on Windows/Linux  
**Project Type**: Python library-style pipeline module with CLI-invokable entrypoint integration  
**Performance Goals**: Process a typical <=50-page PDF profile in <=5 seconds on standard developer hardware; deterministic repeated output for identical input  
**Constraints**: No LLM inference for `origin_type` and `layout_complexity`; deterministic and unit-testable output; Stage 1 only (no extraction implementation)  
**Scale/Scope**: Stage 1 triage for heterogeneous enterprise PDFs, designed to route future Stage 2 strategies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase-0 Gate Assessment

- `Architecture`: PASS. Plan enforces typed `DocumentProfile` boundary and interface-based strategy for domain classification.
- `Testing`: PASS. Plan defines deterministic and unit test coverage for all triage decisions.
- `Provenance`: PASS (Stage-scoped). Stage 1 emits profile/routing signals only and does not emit extracted answer units; provenance fields are delegated to extraction stages by design.
- `Escalation Guard`: PASS. Low-confidence or conflicting signals route to higher-cost extraction classes deterministically.
- `Performance/Cost`: PASS. Fast-text-first routing with deterministic escalation path and cost class output.
- `Observability`: PASS. Stage logs strategy decision trace and profiling duration for auditability.

### Post-Phase-1 Re-Check

- `Architecture`: PASS. Data model and contracts preserve strict typed boundaries and pluggable domain strategy.
- `Testing`: PASS. Quickstart and contract artifacts include test cases for deterministic behavior and classifier mapping.
- `Provenance`: PASS (Stage-scoped, unchanged). No extraction payloads are emitted in Stage 1.
- `Escalation Guard`: PASS. Cost resolver contract encodes fail-closed escalation.
- `Performance/Cost`: PASS. Cost class mapping is deterministic and explicit.
- `Observability`: PASS. Contract captures required triage audit fields and persistence artifact.

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
|   |   `-- document_profile.py
|   `-- triage/
|       |-- pdf_stats_analyzer.py
|       |-- origin_classifier.py
|       |-- layout_classifier.py
|       |-- domain/
|       |   |-- strategy.py
|       |   `-- keyword_strategy.py
|       `-- extraction_cost_resolver.py

tests/
|-- unit/
|   |-- test_origin_classifier.py
|   |-- test_layout_classifier.py
|   |-- test_extraction_cost_resolver.py
|   `-- test_document_profile_serialization.py
`-- fixtures/
    `-- pdf_samples/
```

**Structure Decision**: Single Python project structure with modular triage package and unit-test-first layout. This matches repository scope and constitution requirements while keeping stage boundaries explicit.

## Complexity Tracking

No constitution violations requiring justification.
