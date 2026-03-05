## The Document Intelligence Refinery

# 1. Executive Summary

The goal of this project is to build **The Document Intelligence Refinery** — a production-grade, multi-stage, agentic document processing pipeline capable of transforming heterogeneous enterprise documents into structured, queryable, provenance-preserving knowledge.

This is **not** a PDF-to-text script.

It is a classification-aware, multi-strategy extraction system that:

- Preserves document structure
- Prevents RAG hallucinations via semantic chunking
- Tracks spatial provenance (page + bounding box)
- Escalates intelligently from cheap extraction to vision models
- Supports structured SQL queries over extracted facts
- Produces audit-ready citation chains

The target outcome is an FDE-grade architecture that can onboard new document types with configuration changes — not code rewrites.

# 2. The Core Problem

Enterprise intelligence is trapped inside:

- Native digital PDFs
- Scanned image-based PDFs
- Multi-column reports
- Table-heavy financial documents
- Technical assessments
- Government audit reports

Three systemic failure modes must be solved:

## 2.1 Structure Collapse

Traditional OCR flattens:

- Multi-column layouts
- Tables
- Headers
- Footnotes
- Figures

Result: syntactically present but semantically useless text.

## 2.2 Context Poverty

Naive token-based chunking:

- Splits tables across chunks
- Separates figures from captions
- Breaks numbered lists
- Destroys logical units

Result: RAG hallucinations.

## 2.3 Provenance Blindness

Most systems cannot answer:

> "Exactly where in the 400-page report does this number come from?"

Without spatial provenance, data is not auditable or trustworthy.

# 3. System Overview — The 5-Stage Refinery Pipeline

**Input → Multi-Stage Processing → Structured Output**

## 3.1 Inputs

The system must handle:

- Native PDFs
- Scanned PDFs
- Table-heavy financial reports
- Technical assessment reports
- Structured fiscal documents
- Images containing text

## 3.2 Stage 1 — Triage Agent (Document Classifier)

Before extraction, every document must be profiled.

### Output: `DocumentProfile`

Classification dimensions:

- `origin_type`: native_digital | scanned_image | mixed | form_fillable
- `layout_complexity`: single_column | multi_column | table_heavy | figure_heavy | mixed
- `language`: detected language + confidence
- `domain_hint`: financial | legal | technical | medical | general
- `estimated_extraction_cost`: fast_text_sufficient | needs_layout_model | needs_vision_model

The profile determines downstream routing strategy.

Profiles must be saved in:

```
.refinery/profiles/{doc_id}.json
```

## 3.3 Stage 2 — Multi-Strategy Extraction Layer

Three extraction strategies must be implemented.

### Strategy A — Fast Text (Low Cost)

Tools: pdfplumber / pymupdf

Triggers when:

- `origin_type = native_digital`
- `layout_complexity = single_column`

Must compute:

- Character density
- Image-to-page area ratio
- Character count per page
- Confidence score

If confidence is LOW → automatic escalation.

### Strategy B — Layout-Aware (Medium Cost)

Tools: MinerU or Docling

Triggers when:

- Multi-column layout
- Table-heavy content
- Mixed origin

Must output:

- Text blocks with bounding boxes
- Tables as structured JSON
- Figures with captions
- Reconstructed reading order

### Strategy C — Vision-Augmented (High Cost)

Tools: Vision Language Model (e.g., GPT-4o-mini, Gemini Flash)

Triggers when:

- Scanned PDF
- Confidence failure from Strategy A
- Handwriting detected

Must include:

- Budget guard (cost cap per document)
- Token spend logging
- Cost estimation per document

## Mandatory Escalation Guard

Strategy A must:

- Measure extraction confidence
- Automatically escalate if below threshold
- Never pass low-quality output downstream

No stage may silently degrade output quality.

## Extraction Ledger

Every extraction event must be logged in:

```
.refinery/extraction_ledger.jsonl
```

Each ledger entry must include:

- strategy_used
- confidence_score
- cost_estimate
- processing_time
- escalation_flag

# 4. Stage 3 — Semantic Chunking Engine

Raw extraction is not RAG-ready.

The system must convert extracted content into:

## Logical Document Units (LDUs)

Each LDU must contain:

- `content`
- `chunk_type`
- `page_refs`
- `bounding_box`
- `parent_section`
- `token_count`
- `content_hash`

## Chunking Constitution (Enforceable Rules)

The system must enforce:

- Table header row remains attached to all table rows
- Table cells are never split across chunks
- Figure captions are stored as metadata of figure chunks
- Numbered lists remain intact unless exceeding `max_tokens`
- Section headers propagate as parent metadata
- Cross-references are resolved and linked
- Every chunk includes spatial provenance

A `ChunkValidator` must validate all invariants before emitting LDUs.

# 5. Stage 4 — PageIndex Builder

A hierarchical navigation tree over the document.

Each `PageIndexNode` must include:

- `title`
- `page_start`
- `page_end`
- `child_sections`
- `key_entities`
- `summary` (2–3 sentences, LLM-generated)
- `data_types_present` (tables, figures, equations, etc.)

Purpose:

Enable section-level navigation before vector search.

Stored in:

```
.refinery/pageindex/{doc_id}.json
```

# 6. Stage 5 — Query Interface Agent

A LangGraph-based agent with three tools:

- `pageindex_navigate`
- `semantic_search`
- `structured_query` (SQL over fact table)

All responses must include a:

## ProvenanceChain

Each citation must contain:

- `document_name`
- `page_number`
- `bounding_box`
- `content_hash`

No answer may be returned without provenance.

# 7. Fact Table Extraction

For numerical and financial documents:

Extract key-value facts into SQLite.

Examples:

- revenue: $4.2B
- fiscal_year: 2024
- capital_expenditure_q3: value

This enables precise structured querying separate from vector search.

# 8. Target Corpus Requirements

The pipeline must successfully process at least four document classes:

1. Annual Financial Report (native digital, multi-column)
2. Scanned Government/Legal Report (image-based)
3. Technical Assessment Report (mixed content)
4. Structured Fiscal Data Report (table-heavy)

The system must generalize beyond the provided corpus.

# 9. Evaluation Criteria

High-scoring systems demonstrate:

- Confidence-gated escalation working correctly
- Table extraction fidelity
- Full bounding box provenance
- PageIndex improving retrieval precision
- Budget guard enforced
- Clean modular architecture
- Configuration-driven extensibility

# 10. Architectural Expectations

The system must:

- Use Pydantic models for all core schemas
- Use Strategy Pattern for extraction
- Separate agents from strategies
- Externalize thresholds in `extraction_rules.yaml`
- Log observability artifacts
- Support onboarding new document types via config changes only

# 11. Engineering Philosophy

The objective is not to build a PDF parser.

The objective is to build a system that:

- Degrades gracefully
- Escalates intelligently
- Preserves spatial provenance
- Enables auditability
- Can onboard new document domains within 24 hours

This is a production-grade document intelligence architecture project.
