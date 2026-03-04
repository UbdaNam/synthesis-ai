# Quickstart: Stage 1 Triage Agent Plan Validation

## Prerequisites

- Python environment matching project requirement (`>=3.14`)
- Dependencies installed for planning and tests (`pytest`, `pydantic`, `pdfplumber`, `langgraph`)
- Working directory: `C:\Abdu\synthesis-ai`

## Artifacts Produced in This Plan Phase

- `C:\Abdu\synthesis-ai\specs\001-triage-document-profile\plan.md`
- `C:\Abdu\synthesis-ai\specs\001-triage-document-profile\research.md`
- `C:\Abdu\synthesis-ai\specs\001-triage-document-profile\data-model.md`
- `C:\Abdu\synthesis-ai\specs\001-triage-document-profile\contracts\triage-node-contract.md`
- `C:\Abdu\synthesis-ai\specs\001-triage-document-profile\contracts\document-profile.schema.json`

## Implementation Startup Steps

1. Create module skeleton under `src/synthesis_ai/` per `plan.md` structure.
2. Implement typed models (`GraphState`, `DocumentProfile`, nested signal models).
3. Implement deterministic analyzers/classifiers:
   - `PDFStatsAnalyzer`
   - `OriginClassifier`
   - `LayoutClassifier`
   - `DomainClassifierStrategy` + default keyword strategy
   - `ExtractionCostResolver`
4. Implement triage LangGraph first-node integration.
5. Implement profile persistence to `.refinery/profiles/{doc_id}.json`.

## Minimum Test Suite

Run from repository root:

```powershell
python -m pytest -q
```

Required unit tests:
- origin detection (`native_digital`, `scanned_image`, `mixed`, `form_fillable`)
- layout detection (`single_column`, `multi_column`, `table_heavy`, `figure_heavy`, `mixed`)
- extraction cost mapping
- profile serialization and deterministic rerun equality

## Acceptance Check

A document run is acceptable when:
- graph state exits triage with non-null `document_profile`
- persisted profile exists at `.refinery/profiles/{doc_id}.json`
- profile validates against `document-profile.schema.json`
- repeated runs on same input produce identical profile JSON
