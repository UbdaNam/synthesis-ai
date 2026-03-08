# Implementation Plan: Query Agent and Provenance Layer

**Branch**: `005-query-agent-provenance` | **Date**: 2026-03-08 | **Spec**: [spec.md](C:/Abdu/synthesis-ai/specs/005-query-agent-provenance/spec.md)
**Input**: Feature specification from `/specs/005-query-agent-provenance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build Stage 5 as a real LangGraph tool-calling query agent that consumes persisted PageIndex artifacts, retrieval-ready LDUs, and a SQLite-backed FactTable to answer grounded questions and verify claims. The implementation uses explicit shared state, exactly three attached tools (`pageindex_navigate`, `semantic_search`, `structured_query`), OpenRouter-backed tool-calling chat inference, typed final answer models with provenance enforcement, and fail-closed audit classification.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**: `langgraph`, `langchain-core`, `langchain-openrouter`, `langchain-openai` (OpenAI-compatible embeddings client via OpenRouter), `chromadb`, `pydantic`, `pyyaml`, standard-library `sqlite3`  
**Storage**: Persisted PageIndex JSON under `.refinery/pageindex/`, local Chroma collection under `.refinery/pageindex/chroma`, SQLite FactTable under `.refinery/query/facts.db`  
**Testing**: `pytest`  
**Target Platform**: Local Python runtime on Windows/Linux/macOS with filesystem access to persisted artifacts  
**Project Type**: Single-project LangGraph application component  
**Performance Goals**: Section-targeted question answering should usually complete in one navigation step plus bounded retrieval, and structured fact lookups should resolve through SQLite without full semantic search  
**Constraints**: No final answer without provenance unless classified `not_found` or `unverifiable`; runtime must not depend on MCP; exactly three tools attached to the model; fail closed on missing evidence, missing provenance, or invalid answer shape  
**Scale/Scope**: Single processed document per query session, documents with hundreds of LDUs and nested PageIndex sections, numerical documents requiring exact fact retrieval and claim verification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Typed Contracts`: PASS. The stage will add explicit Pydantic models for provenance items, final query results, audit results, FactTable rows, and tool IO envelopes. Retrieval tool outputs will be normalized before the agent consumes them.
- `Determinism`: PASS. Query-path preference (`pageindex_navigate` first for broad/section questions, `structured_query` for numerical fact requests, `semantic_search` for narrative evidence retrieval) will be encoded outside the LLM; the LLM is limited to tool selection within the three-tool boundary and final grounded synthesis.
- `Architecture`: PASS. `query_agent.py` will orchestrate LangGraph state transitions; tools live under `src/query/tools/`; fact extraction and audit mode remain separate modules; models stay under `src/models/`.
- `Provenance`: PASS. Final response models will require provenance items for supported answers. Tool outputs will preserve `document_name`, `page_number`, `bounding_box`, and `content_hash` from PageIndex, LDU, and FactTable source linkage.
- `Escalation Guard`: PASS. The query agent will fail closed when the selected path cannot supply sufficient provenance or when the final typed response would otherwise violate answer-grounding rules.
- `Performance/Cost`: PASS. The plan uses section narrowing first, SQL for precise fact retrieval, bounded semantic search, and a configurable OpenRouter tool-calling model to avoid unnecessary large-context generation.
- `Validation and Tests`: PASS. Unit tests cover each tool, provenance contracts, SQLite fact queries, and audit classification; integration tests cover full question-to-answer and claim-verification flows with real persisted artifacts.
- `Operability`: PASS. Query execution metadata, retrieval path used, and structured failure categories will be persisted or surfaced through stage outputs for debugging and auditability.

## Project Structure

### Documentation (this feature)

```text
specs/005-query-agent-provenance/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── agents/
│   └── query_agent.py
├── models/
│   ├── provenance_chain.py
│   └── query_result.py
├── query/
│   ├── audit_mode.py
│   ├── fact_table_extractor.py
│   └── tools/
│       ├── pageindex_navigate.py
│       ├── semantic_search.py
│       └── structured_query.py

tests/
├── integration/
└── unit/
```

**Structure Decision**: Extend the existing single-project LangGraph layout. Keep orchestration in `src/agents/`, contracts in `src/models/`, and Stage 5 retrieval infrastructure in `src/query/` so the query layer remains isolated from extraction, chunking, and indexing implementations.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
