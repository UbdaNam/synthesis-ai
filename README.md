# synthesis-ai
Agentic Document Processing at Scale

## Stage 1 Triage Agent

Current implementation includes a deterministic Stage 1 triage node that:

- analyzes PDF signals (character density, image ratio, layout signals)
- classifies origin/layout/domain/language/extraction-cost into a typed `DocumentProfile`
- persists profile JSON to `.refinery/profiles/{doc_id}.json`
- appends observability entries to `.refinery/profiling_ledger.jsonl`

Run local demo with:

```powershell
python main.py
```

## Stage 2 Structure Extraction Layer

Stage 2 now runs immediately after triage in LangGraph (`triage -> extract`) and:

- routes deterministically from `DocumentProfile` to `fast_text`, `layout_aware`, or `vision`
- applies confidence-gated escalation (`fast_text -> layout_aware -> vision`)
- enforces fail-closed behavior for low confidence and budget-cap violations
- emits normalized `ExtractedDocument` payloads with provenance (`page_number`, `bounding_box`, `content_hash`)
- appends attempt-level audit entries to `.refinery/extraction_ledger.jsonl`
- invokes Vision extraction through a real OpenRouter-backed LangChain chat model when routing/escalation reaches `vision`

Main configuration lives in `rubric/extraction_rules.yaml` under `extraction.*`.
Environment variables are auto-loaded from `.env` at runtime.

Layout Strategy B is configured to use **Docling** by default:

- `extraction.layout_aware.provider: docling` in `rubric/extraction_rules.yaml`
- implementation adapter in `src/strategies/layout_aware.py`

Install/update dependencies after pulling changes:

```powershell
uv sync
```

To enable real vision calls, configure environment variables (see `.env.example`):

```powershell
$env:OPENROUTER_API_KEY="<your_key>"
```

Run Stage 2 focused tests with:

```powershell
python -m pytest tests/unit tests/integration -q
```
