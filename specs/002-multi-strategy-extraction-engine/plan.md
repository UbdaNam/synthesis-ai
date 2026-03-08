# Implementation Plan: Stage 2 Structure Extraction Layer

**Branch**: `002-multi-strategy-extraction-engine` | **Date**: 2026-03-07 | **Spec**: [spec.md](/c:/Abdu/synthesis-ai/specs/002-multi-strategy-extraction-engine/spec.md)
**Input**: Feature specification from `/specs/002-multi-strategy-extraction-engine/spec.md`

## Summary

Implement Stage 2 extraction as a deterministic LangGraph stage after triage.

- Input: `GraphState.document_profile` from Stage 1.
- Output: normalized `ExtractedDocument` in graph state.
- Router: deterministic, non-LLM strategy selection + confidence-gated escalation.
- VisionExtractor: multimodal via OpenRouter through a LangGraph node method using model invocation with structured prompts and structured output parsing.

## Technical Context

**Language/Version**: Python >=3.14  
**Primary Dependencies**: pydantic, langgraph, langchain messages/model interfaces, pyyaml, pdfplumber or pymupdf, MinerU or Docling adapter, OpenRouter model adapter, pytest  
**Storage**: `C:/Abdu/synthesis-ai/rubric/extraction_rules.yaml` and `C:/Abdu/synthesis-ai/.refinery/extraction_ledger.jsonl`  
**Testing**: pytest unit + integration + deterministic/reliability checks  
**Target Platform**: Windows/Linux Python runtime  
**Project Type**: LangGraph stateful pipeline stage  
**Performance Goals**: Deterministic routing, bounded escalation, budget-safe vision usage, attempt-level timing/cost visibility  
**Constraints**: fail closed on low confidence and budget violations; provenance required for emitted segments  
**Scale/Scope**: Per-document Stage 2 extraction only

## Constitution Check

_Gate: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Pre-Phase-0 Gate Assessment

- `Architecture`: PASS. Strategy pattern + typed model boundaries + agent/strategy separation.
- `Testing`: PASS. Unit tests for confidence/escalation; integration tests for state flow and fail-closed behavior.
- `Provenance`: PASS. `page_number`, `bounding_box`, and `content_hash` are required in normalized output.
- `Escalation Guard`: PASS. Deterministic thresholds and fail-closed terminal behavior.
- `Performance/Cost`: PASS. Fast-text-first policy and configurable per-document vision budget cap.
- `Observability`: PASS. Attempt-level ledger fields and processing-time capture.

### Post-Phase-1 Re-Check

- `Architecture`: PASS. `GraphState` and extraction payloads remain typed.
- `Testing`: PASS. Design outputs define tests for routing, structured-output parsing, escalation, and budget cap.
- `Provenance`: PASS. Output contract enforces provenance fields.
- `Escalation Guard`: PASS. A->B->C order and thresholds are config-driven.
- `Performance/Cost`: PASS. Vision token accounting, cost estimation, and cap enforcement are explicit.
- `Observability`: PASS. Ledger contract includes strategy/confidence/cost/time/escalation/rule reference.

## Project Structure

### Documentation (this feature)

```text
C:/Abdu/synthesis-ai/specs/002-multi-strategy-extraction-engine/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- extracted-document.schema.json
|   |-- extraction-ledger-entry.schema.json
|   `-- extractor-node-contract.md
`-- tasks.md
```

### Source Code (repository root)

```text
C:/Abdu/synthesis-ai/
|-- src/
|   |-- models/extracted_document.py
|   |-- agents/extractor.py
|   |-- strategies/base.py
|   |-- strategies/fast_text.py
|   |-- strategies/layout_aware.py
|   |-- strategies/vision.py
|   `-- graph/graph.py
|-- rubric/extraction_rules.yaml
|-- .refinery/extraction_ledger.jsonl
`-- tests/unit/, tests/integration/
```

**Structure Decision**: Single Python project with LangGraph orchestrating triage -> extraction.

## VisionExtractor Requirements (Explicit)

- **Provider path**: OpenRouter multimodal model.
- **LangGraph method**: Vision call occurs in extraction node function (`state`, `config`) and model invocation receives graph config where needed.
- **Triggers**:
  - `origin_type = scanned_image`
  - Strategy A/B confidence below threshold
  - handwriting detected
- **Prompting**: structured extraction prompt template + schema-constrained response.
- **Budget guard**:
  - track token usage per document
  - estimate per-attempt and cumulative cost
  - enforce configurable budget cap from YAML with fail-closed behavior on overflow.

## Complexity Tracking

No constitution violations requiring justification.
