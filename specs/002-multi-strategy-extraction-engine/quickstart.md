# Quickstart: Stage 2 Structure Extraction Layer

## Prerequisites

- Python >=3.14
- Stage 1 outputs `DocumentProfile` in `GraphState`
- Working directory: `C:\Abdu\synthesis-ai`
- Set OpenRouter credentials (see `C:\Abdu\synthesis-ai\.env.example`)

## Required Files

- `C:\Abdu\synthesis-ai\src\models\extracted_document.py`
- `C:\Abdu\synthesis-ai\src\agents\extractor.py`
- `C:\Abdu\synthesis-ai\src\strategies\base.py`
- `C:\Abdu\synthesis-ai\src\strategies\fast_text.py`
- `C:\Abdu\synthesis-ai\src\strategies\layout_aware.py`
- `C:\Abdu\synthesis-ai\src\strategies\vision.py`
- `C:\Abdu\synthesis-ai\src\graph\graph.py`
- `C:\Abdu\synthesis-ai\rubric\extraction_rules.yaml`
- `C:\Abdu\synthesis-ai\.refinery\extraction_ledger.jsonl`

## LangGraph Method for VisionExtractor

- Implement extraction as a graph node function that accepts `state` and optional `config`.
- Perform multimodal model invocation inside node execution.
- Pass graph config into async model call where required (`ainvoke(..., config)` pattern).
- Use structured prompt + schema-constrained output parsing before normalizing to `ExtractedDocument`.

## Trigger Rules

VisionExtractor triggers when:
- `origin_type = scanned_image`
- Strategy A/B confidence below configured threshold
- handwriting detection is true

## Budget Guard

- Track token usage per document across vision attempts.
- Estimate per-attempt and cumulative cost.
- Enforce configurable per-document cap from YAML.
- On cap violation: log ledger entry and fail closed.

## Configuration Keys

- `extraction.fast_text.*`
- `extraction.escalation.acceptance_thresholds.*`
- `extraction.vision.model`
- `extraction.vision.budget_cap_default`
- `extraction.vision.tokens_per_page_estimate`
- `extraction.vision.cost_per_1k_tokens`
- `extraction.router.rule_version`

## Validation Commands

```powershell
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python -m pytest -q
python main.py sample_files/background-checks.pdf --doc-id quickstart-stage2
```
