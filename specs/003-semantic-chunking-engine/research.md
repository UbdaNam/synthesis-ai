# Research: Semantic Chunking Engine

## Decision: Use deterministic structural traversal rather than token-window chunking

Rationale: Stage 3 must preserve tables, figures, lists, and section context,
so the engine should traverse `TextBlock`, `StructuredTable`, and `FigureBlock`
in document reading order and build chunks from structural units first. This
aligns with the constitution's determinism-first rule and avoids meaning loss
caused by naive token slicing.

Alternatives considered:
- Sliding token windows over raw text only: rejected because table/header and
  figure/caption relationships would be broken.
- LLM-guided semantic chunking: rejected because Stage 3 requires deterministic,
  auditable behavior without model variance or added cost.

## Decision: Define explicit `LDU` and `ChunkRelationship` Pydantic contracts

Rationale: Stage 3 is a new typed boundary in the LangGraph pipeline. `LDU`
must carry content, chunk type, page refs, bounding box, parent section, token
count, content hash, relationships, and metadata. `ChunkRelationship` should
carry typed links such as `references_table`, `references_figure`,
`references_section`, `belongs_to_section`, and `follows`.

Alternatives considered:
- Reusing untyped dictionaries in state: rejected because the constitution
  forbids raw payload handoff between stages.
- Embedding relationships as free-form metadata only: rejected because it makes
  validation and downstream interpretation weaker.

## Decision: Count tokens with a single deterministic lexical strategy

Rationale: Stage 3 needs stable chunk boundaries and repeatable tests. A single
  deterministic token counter should be used across all chunk types and tests,
  based on normalized lexical splitting rather than model-specific tokenization.

Alternatives considered:
- Provider tokenizer parity: rejected because Stage 3 introduces no model calls
  and would gain an unnecessary dependency.
- Character-count thresholds: rejected because list/table chunking decisions need
  a more semantically meaningful unit than characters.

## Decision: Split oversized tables by row groups and repeat headers in every derived chunk

Rationale: This is the simplest deterministic way to guarantee the rule that no
table cell is separated from its header row. Header repetition also keeps table
sub-chunks self-contained for retrieval.

Alternatives considered:
- Splitting tables by arbitrary token windows: rejected because header context
  would be lost.
- Storing giant tables as a single chunk regardless of size: rejected because it
  violates chunk-size constraints and retrieval usability.

## Decision: Group consecutive numbered list items into one logical unit unless threshold is exceeded

Rationale: Numbered lists represent one semantic structure. Grouping adjacent
`list_item` blocks preserves continuity and only splits when a configured token
threshold requires it, while carrying continuity metadata across derived chunks.

Alternatives considered:
- Treating each list item as an independent chunk by default: rejected because it
  loses sequence context and weakens retrieval fidelity.
- Merging lists with surrounding paragraphs: rejected because it blurs
  structural boundaries.

## Decision: Resolve references with deterministic pattern matching plus known-chunk lookup

Rationale: Cross-references like `see Table 3`, `refer to Figure 2`, and
`Section 4.1` can be resolved using consistent regex-style detection and a known
catalog of chunk identifiers or ordinal labels derived during chunk creation.

Alternatives considered:
- Leaving references as plain text only: rejected because the requirements
  explicitly call for stored chunk relationships.
- Fuzzy semantic linking: rejected because it introduces ambiguity and weakens
  reproducibility.

## Decision: Fail closed through explicit `ChunkValidator` enforcement

Rationale: Stage 3 is a governed boundary. Validation must reject missing
required fields, broken table/header association, detached figure captions,
invalid list splits, missing parent-section metadata, and inconsistent
relationships before downstream emission.

Alternatives considered:
- Best-effort chunk emission with warnings only: rejected because low-trust
  output must not pass silently downstream.
- Ad hoc validation inside the engine only: rejected because a dedicated
  validator is easier to test and audit.

## Decision: Integrate Stage 3 as a LangGraph node consuming `GraphState.extracted_document`

Rationale: The feature is explicitly scoped to the existing pipeline and should
build directly on Stage 2 normalized output in state. A dedicated `chunker.py`
entrypoint keeps orchestration separate from chunking logic and preserves clear
stage boundaries.

Alternatives considered:
- A standalone offline chunking script: rejected because it bypasses the staged
  graph contract.
- Reusing the extraction router for chunking: rejected because chunking is a new
  stage with different responsibilities and outputs.
