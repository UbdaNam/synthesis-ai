# Quickstart: Stage 1 Triage Agent (Challenge Structure)

## Prerequisites

- Python >=3.14
- Dependencies for Stage 1: `pydantic`, `pdfplumber`, `langdetect`, `langgraph`, `pytest`
- Working directory: `C:\Abdu\synthesis-ai`

## Required Layout

- `src/models/document_profile.py`
- `src/models/graph_state.py`
- `src/agents/triage.py`
- `src/graph/graph.py`
- `rubric/extraction_rules.yaml`
- `.refinery/profiles/`
- `.refinery/profiling_ledger.jsonl`
- `tests/`

## Stage 1 Implementation Steps

1. Define typed models in `src/models/`.
2. Implement triage orchestration logic in `src/agents/triage.py`.
3. Implement graph assembly in `src/graph/graph.py`.
4. Load thresholds/rules from `rubric/extraction_rules.yaml`.
5. Classify origin/layout/language/domain/cost deterministically.
6. Persist profile JSON to `.refinery/profiles/{doc_id}.json`.
7. Write Stage 1 profiling evidence events to `.refinery/profiling_ledger.jsonl`.

## Run

```powershell
python main.py <pdf-path> --doc-id <id>
```

## Minimum Test Suite

Run from repository root:

```powershell
python -m pytest -q
```

Required tests:
- origin classification correctness
- layout classification correctness
- language detection (English + non-English + confidence bounds)
- domain classification correctness
- extraction cost mapping correctness
- deterministic repeat-run equality (`same doc -> identical profile payload`)
- JSON schema validation for `DocumentProfile`
- profiling ledger entry format/field validation
- graph entrypoint contract validation
- known-sample classification validation

## Acceptance Checks

- Graph compiles from `src/graph/graph.py` with `triage` as entrypoint.
- `main.py` invokes compiled graph and returns output state with `document_profile`.
- Profile persisted at `.refinery/profiles/{doc_id}.json`.
- Profile matches schema contract.
- Repeated runs with same input produce identical classification outputs.
- Profiling entry exists in `.refinery/profiling_ledger.jsonl` with required evidence fields.

## Stage Boundary Note

Stage 1 ends at profile + profiling evidence generation. Extraction logic and extraction artifacts are deferred to Stage 2.

