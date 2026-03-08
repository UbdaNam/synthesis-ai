# synthesis-ai

Production-oriented document intelligence pipeline built as a staged LangGraph
workflow.

The current pipeline has five implemented stages:

1. Stage 1 triage: deterministic document profiling
2. Stage 2 extraction: strategy-based structure extraction
3. Stage 3 chunking: semantic chunk generation for retrieval
4. Stage 4 indexing: PageIndex construction and retrieval preparation
5. Stage 5 query: provenance-aware question answering and audit mode

## Overview

The system processes a document through typed stage boundaries:

- `DocumentProfile` from Stage 1
- `ExtractedDocument` from Stage 2
- `List[LDU]` plus `ChunkRelationship` records from Stage 3
- `PageIndexDocument` from Stage 4
- `QueryResult` plus `ProvenanceChain` records from Stage 5

Each stage is governed by the engineering rules in
[constitution.md](C:/Abdu/synthesis-ai/.specify/memory/constitution.md):

- typed Pydantic contracts at stage boundaries
- deterministic routing and transformation logic where measurable rules exist
- auditable artifacts and provenance preservation
- fail-closed handling for invalid outputs
- budget-aware use of expensive model-backed strategies

## Pipeline

The compiled document-processing LangGraph flow is:

```text
triage -> extract -> chunk -> index
```

Runtime assembly lives in [graph.py](C:/Abdu/synthesis-ai/src/graph/graph.py).
Stage 5 currently runs as a dedicated query layer over the persisted Stage 4
artifacts and retrieval stores rather than as an inline document-processing node.

### Stage 1: Triage

Implemented in [triage.py](C:/Abdu/synthesis-ai/src/agents/triage.py).

Responsibilities:

- inspect PDF signals such as character density, image ratio, and layout cues
- classify origin, layout complexity, language, domain hint, and extraction cost
- emit a typed `DocumentProfile`
- persist profiling evidence to `.refinery/profiles/` and
  `.refinery/profiling_ledger.jsonl`

### Stage 2: Extraction

Implemented through [extractor.py](C:/Abdu/synthesis-ai/src/agents/extractor.py)
and the strategy modules under `src/strategies/`.

Responsibilities:

- route deterministically to `fast_text`, `layout_aware`, or `vision`
- apply confidence-gated escalation
- fail closed on low-confidence or blocked outcomes
- emit a normalized `ExtractedDocument`
- append extraction attempts to `.refinery/extraction_ledger.jsonl`

Current extraction strategies:

- `fast_text`: native digital PDF text extraction
- `layout_aware`: Docling-backed structural extraction
- `vision`: OpenRouter-backed multimodal fallback

### Stage 3: Semantic Chunking

Implemented in [chunker.py](C:/Abdu/synthesis-ai/src/agents/chunker.py) and the
modules under `src/chunking/`.

Responsibilities:

- consume `ExtractedDocument` directly from `GraphState`
- build typed `LDU` records in reading order
- preserve section context, table headers, figure captions, numbered-list
  continuity, and cross-references
- validate chunking invariants with fail-closed behavior
- append run-level entries to `.refinery/chunking_ledger.jsonl`

### Stage 4: PageIndex Builder

Implemented in [indexer.py](C:/Abdu/synthesis-ai/src/agents/indexer.py) and the
modules under `src/indexing/`.

Responsibilities:

- consume validated `List[LDU]` directly from `GraphState`
- build a hierarchical `PageIndexDocument` with typed `PageIndexNode` records
- generate bounded OpenRouter summaries for each section using only
  section-local chunks
- detect deterministic section entities and `data_types_present`
- persist PageIndex artifacts to `.refinery/pageindex/{doc_id}.json`
- ingest LDU content into a local Chroma collection for Stage 5 section-first
  retrieval preparation
- fail closed on invalid trees, invalid summaries, or vector-ingestion errors

### Stage 5: Query Agent and Provenance Layer

Implemented in [query_agent.py](C:/Abdu/synthesis-ai/src/agents/query_agent.py)
and the modules under `src/query/`.

Responsibilities:

- accept natural-language questions or audit-mode claims against processed
  documents
- use exactly three real tools:
  - `pageindex_navigate`
  - `semantic_search`
  - `structured_query`
- route deterministically toward section-first retrieval, semantic evidence
  retrieval, or precise fact lookup
- return typed `QueryResult` outputs with explicit provenance for supported
  answers
- maintain a SQLite FactTable under `.refinery/query/facts.db`
- fail closed to `not_found` or `unverifiable` when evidence is insufficient or
  invalid

## Core Models

Key models live under `src/models/`:

- [document_profile.py](C:/Abdu/synthesis-ai/src/models/document_profile.py)
- [extracted_document.py](C:/Abdu/synthesis-ai/src/models/extracted_document.py)
- [ldu.py](C:/Abdu/synthesis-ai/src/models/ldu.py)
- [chunk_relationship.py](C:/Abdu/synthesis-ai/src/models/chunk_relationship.py)
- [page_index.py](C:/Abdu/synthesis-ai/src/models/page_index.py)
- [provenance_chain.py](C:/Abdu/synthesis-ai/src/models/provenance_chain.py)
- [query_result.py](C:/Abdu/synthesis-ai/src/models/query_result.py)
- [graph_state.py](C:/Abdu/synthesis-ai/src/models/graph_state.py)

## Configuration

Pipeline rules live in
[extraction_rules.yaml](C:/Abdu/synthesis-ai/rubric/extraction_rules.yaml).

Current top-level configuration sections:

- `triage`: deterministic profiling thresholds and domain rules
- `extraction`: Stage 2 routing, provider, escalation, and cost settings
- `chunking`: Stage 3 chunk size, table/list splitting, reference resolution,
  and ledger settings
- `pageindex`: Stage 4 summary model, artifact paths, entity extraction,
  section ranking, and vector-ingestion settings including the OpenRouter
  embedding model
- `query`: Stage 5 model, fact-table, and retrieval limits for the Query Agent

Environment variables are loaded from `.env` at runtime through
[env.py](C:/Abdu/synthesis-ai/src/config/env.py).

Important environment variable:

- `OPENROUTER_API_KEY`: required for the Stage 2 vision strategy and all Stage
  4/Stage 5 model-backed operations
- `QUERY_FACTS_DB_PATH`: optional override for the Stage 5 SQLite FactTable path

Use [.env.example](C:/Abdu/synthesis-ai/.env.example) as the reference for local
configuration.

## Installation

This project targets Python `>=3.14`.

Install dependencies with:

```powershell
uv sync
```

If you are using a virtual environment directly:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .[dev]
```

## Running the Pipeline

The local entrypoint is [main.py](C:/Abdu/synthesis-ai/main.py).

Run the default sample:

```powershell
python main.py
```

Run a specific file:

```powershell
python main.py "sample_files/Orakly NOV Invoice.pdf" --doc-id "Orakly NOV Invoice"
```

Run a grounded question after the document pipeline completes:

```powershell
python main.py "sample_files/background-checks.pdf" --doc-id "background-checks" --query "What does the report say about financial results?"
```

Run audit mode:

```powershell
python main.py "sample_files/background-checks.pdf" --doc-id "background-checks" --query "Revenue is USD 1250000." --audit
```

The runtime prints selected stage outputs, including extraction status, chunk
relationship data, indexing failures, and optional Stage 5 query results.

## Artifacts

Pipeline runs write artifacts under `.refinery/`.

Important outputs:

- `.refinery/profiles/*.json`: Stage 1 profile snapshots
- `.refinery/profiling_ledger.jsonl`: Stage 1 profiling ledger
- `.refinery/extraction_ledger.jsonl`: Stage 2 extraction ledger
- `.refinery/chunking_ledger.jsonl`: Stage 3 chunking ledger
- `.refinery/pageindex/*.json`: Stage 4 persisted PageIndex artifacts
- `.refinery/pageindex/chroma/`: Stage 4 local vector persistence
- `.refinery/query/facts.db`: Stage 5 SQLite FactTable
- `.refinery/query/ldu_cache/*.json`: Stage 5 LDU cache for provenance recovery

These artifacts are intended for inspection, debugging, and auditability.

## Testing

Run the full test suite:

```powershell
python -m pytest
```

Run Stage 2 focused tests:

```powershell
python -m pytest tests/unit tests/integration -q
```

Run Stage 3 focused tests:

```powershell
python -m pytest tests/unit/test_*chunk* tests/integration/test_chunker_* -q
```

Run Stage 4 focused tests:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_*pageindex* tests/integration/test_pageindex_* -q --basetemp=.test_tmp/pytest-stage4
```

Run Stage 5 focused tests:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_*query* tests/unit/test_*fact* tests/unit/test_provenance_chain.py tests/integration/test_query_agent_* -q --basetemp=.test_tmp/pytest-stage5
```

## Repository Layout

```text
src/
|-- agents/        # LangGraph stage entrypoints
|-- chunking/      # Stage 3 deterministic chunk construction and validation
|-- config/        # environment loading
|-- graph/         # graph assembly
|-- indexing/      # Stage 4 PageIndex building, summarization, and vector ingestion
|-- models/        # typed contracts
|-- query/         # Stage 5 tools, FactTable extraction, and audit logic
`-- strategies/    # Stage 2 extraction strategies

tests/
|-- integration/
`-- unit/

rubric/
`-- extraction_rules.yaml

.refinery/         # persisted profiling, extraction, chunking, indexing, and query artifacts
specs/             # spec-driven planning artifacts
```

## Development Notes

- Keep stage boundaries typed. Do not pass raw provider payloads between stages.
- Prefer deterministic logic over model reasoning when measurable rules are
  sufficient.
- Treat validator failures as hard stops, not warnings.
- Keep new work aligned with the stage-specific planning artifacts under
  `specs/`.
