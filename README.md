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
