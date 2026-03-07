# Implementation Plan: Semantic Chunking Engine

**Branch**: `003-semantic-chunking-engine` | **Date**: 2026-03-07 | **Spec**: [spec.md](C:\Abdu\synthesis-ai\specs\003-semantic-chunking-engine\spec.md)
**Input**: Feature specification from `/specs/003-semantic-chunking-engine/spec.md`

## Summary

Build Stage 3 as a deterministic Semantic Chunking Engine that consumes the
existing Stage 2 `ExtractedDocument` from LangGraph state, traverses structural
content in reading order, emits validated `List[LDU]`, and records auditable
chunking outcomes without expanding scope into indexing, vector storage, fact
extraction, or query-time behavior.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**: Pydantic 2.11+, LangGraph 0.3+, PyYAML 6+, pytest 8+  
**Storage**: Filesystem artifacts and YAML configuration under `rubric/` and `.refinery/`  
**Testing**: pytest unit and integration suites  
**Target Platform**: Local and server-side Python runtime executing LangGraph pipelines  
**Project Type**: Single-project Python pipeline/library  
**Performance Goals**: Deterministic chunking of a single extracted document within one pipeline step, with stable output ordering and bounded chunk sizes driven by configuration  
**Constraints**: Must consume `ExtractedDocument` directly from LangGraph state; no raw provider payloads; no LLM-dependent chunking logic; fail closed on invalid output; preserve provenance on every emitted LDU; keep scope limited to Stage 3 only  
**Scale/Scope**: One new LangGraph stage, new Stage 3 models and chunking modules, Stage 3 rule additions in `rubric/extraction_rules.yaml`, and focused unit/integration coverage for mixed-content documents

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

- `Typed Contracts`: PASS. Stage 3 is designed around explicit `LDU` and
  `ChunkRelationship` Pydantic contracts, plus state-level typed outputs for
  LangGraph handoff.
- `Determinism`: PASS. Chunking, section propagation, reference detection, token
  counting, and hash generation are deterministic and rule-driven outside any
  LLM.
- `Architecture`: PASS. `src/agents/chunker.py` orchestrates, `src/chunking/`
  performs bounded transformation/validation work, and `src/models/` defines
  contracts.
- `Provenance`: PASS. Stage 3 design carries forward page references, bounding
  boxes, upstream content hashes, and deterministic Stage 3 content hashes.
- `Escalation Guard`: PASS. Invalid chunk outputs fail closed; no silent fallback
  to naive windowing is permitted.
- `Performance/Cost`: PASS. Stage 3 introduces no model calls and uses
  configuration-based chunk limits rather than expensive runtime escalation.
- `Validation and Tests`: PASS. Plan includes unit tests for every governed rule
  plus integration tests for `ExtractedDocument -> ChunkingEngine -> List[LDU]`.
- `Operability`: PASS. Stage 3 will emit auditable chunking artifacts and clear
  failure categories suitable for persisted logs and inspection.

## Project Structure

### Documentation (this feature)

```text
specs/003-semantic-chunking-engine/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- chunker-node-contract.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/
|-- agents/
|   |-- extractor.py
|   `-- chunker.py
|-- chunking/
|   |-- engine.py
|   |-- validator.py
|   |-- reference_resolver.py
|   |-- token_counter.py
|   `-- hash_generator.py
|-- graph/
|   `-- graph.py
`-- models/
    |-- graph_state.py
    |-- ldu.py
    `-- chunk_relationship.py

rubric/
`-- extraction_rules.yaml

tests/
|-- integration/
`-- unit/
```

**Structure Decision**: Extend the existing single-project LangGraph pipeline by
adding one new Stage 3 agent node, two new output models, and modular chunking
helpers under `src/chunking/`. Integrate Stage 3 through `GraphState` and
`src/graph/graph.py` so chunking consumes the existing Stage 2 normalized
contract instead of introducing a parallel pipeline entrypoint.

## Phase 0: Research

Research resolved all planning decisions without unresolved clarifications:

1. Deterministic chunk traversal strategy
2. LDU and relationship contract design
3. Token counting strategy
4. Reference resolution behavior
5. Validation boundaries and fail-closed handling
6. LangGraph state integration for Stage 3 outputs

## Phase 1: Design

### Data Model Approach

- Add `LDU` in `src/models/ldu.py` as the canonical Stage 3 output.
- Add `ChunkRelationship` in `src/models/chunk_relationship.py` for table,
  figure, section, and sequencing links.
- Extend `GraphState` to carry chunking outputs, errors, and audit metadata.

### Chunking Architecture

- `src/agents/chunker.py`: public Stage 3 entrypoint; loads Stage 3 rules,
  consumes `state.extracted_document`, invokes engine, validator, and emits
  updated state.
- `src/chunking/engine.py`: reading-order traversal and structural chunk
  formation.
- `src/chunking/reference_resolver.py`: deterministic detection and resolution of
  references such as `Table 3`, `Figure 2`, and `Section 4.1`.
- `src/chunking/token_counter.py`: single deterministic token counting strategy
  used throughout Stage 3.
- `src/chunking/hash_generator.py`: deterministic content-hash generation for
  LDUs from canonicalized content.
- `src/chunking/validator.py`: enforcement of required-field validity, header
  preservation, caption attachment, list integrity, section inheritance, and
  relationship consistency.

### LangGraph Integration

- Consume `ExtractedDocument` directly from `GraphState.extracted_document`.
- Add Stage 3 output fields such as `chunked_document`, `chunking_error`, and
  chunking audit metadata to `GraphState`.
- Update `src/graph/graph.py` to insert `chunk` after `extract`, yielding
  `triage -> extract -> chunk`.

### Configuration Plan

Add a `chunking` section in `rubric/extraction_rules.yaml` with:

- `rule_version`
- `max_tokens_per_chunk`
- `numbered_list_split_threshold`
- `table_row_group_limit`
- `reference_resolution_behavior`
- `section_heading_block_types`
- `chunking_ledger_path`

### Testing Plan

- Unit tests for schema validation, table row grouping with repeated headers,
  figure caption metadata attachment, numbered list preservation/splitting,
  section propagation, reference resolution, token counting, content hash
  stability, and validator failure cases.
- Integration tests for mixed-content `ExtractedDocument` fixtures through
  `ChunkingEngine` and `chunker.py`.

## Post-Design Constitution Check

- `Typed Contracts`: PASS. Design uses new Pydantic models and typed state
  fields only.
- `Determinism`: PASS. Token counting, reference resolution, and traversal rules
  are deterministic by construction.
- `Architecture`: PASS. Orchestration and transformation logic remain separated.
- `Provenance`: PASS. Every emitted LDU preserves provenance and chunk-level
  hashes.
- `Escalation Guard`: PASS. Validator failure blocks downstream emission.
- `Performance/Cost`: PASS. No Stage 3 model budget or dynamic escalation is
  introduced.
- `Validation and Tests`: PASS. Design includes explicit validator and direct
  tests for all five challenge rules.
- `Operability`: PASS. Design includes chunking audit metadata and a persisted
  chunking ledger path in configuration.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| None      | N/A        | N/A                                  |
