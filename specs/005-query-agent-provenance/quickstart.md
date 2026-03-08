# Quickstart: Query Agent and Provenance Layer

## Prerequisites

- A processed document with:
  - Stage 4 PageIndex JSON in `.refinery/pageindex/`
  - retrieval-ready LDUs stored in the local Chroma collection
  - optional numerical facts stored in the Stage 5 SQLite FactTable
- `OPENROUTER_API_KEY` configured in `.env`

## Scenario 1: Grounded Narrative Question

1. Load a processed document with a populated PageIndex artifact.
2. Submit a question such as: `What does the report say about financial results?`
3. Confirm the agent:
   - navigates to the most relevant section first
   - performs semantic retrieval within the narrowed section scope
   - returns a typed answer with at least one provenance entry
4. Verify the final response includes:
   - `answer`
   - `support_status = supported`
   - `retrieval_path_used` containing `pageindex_navigate` and `semantic_search`
   - provenance entries with `document_name`, `page_number`, `bounding_box`, and `content_hash`

## Scenario 2: Numerical Fact Retrieval

1. Populate the SQLite FactTable for a financial document.
2. Submit a question such as: `What is the reported revenue for the fiscal period?`
3. Confirm the agent:
   - classifies the request as fact-heavy
   - invokes `structured_query`
   - returns the exact fact value with provenance linkage to the originating source row and chunk
4. Verify the final response includes `retrieval_path_used` with `structured_query`.

## Scenario 3: Audit Mode - Supported Claim

1. Submit a claim such as: `Revenue increased to 10 million dollars in Q4.`
2. Run the query agent in audit mode.
3. Confirm the result is:
   - `support_status = supported`
   - accompanied by source-backed provenance
   - derived from one or more of the three retrieval tools without using unsupported hidden tools

## Scenario 4: Audit Mode - Not Found or Unverifiable

1. Submit a claim that is absent from the document.
2. Confirm the result is `not_found` and no fabricated supporting evidence is returned.
3. Submit a claim that is ambiguous or only partially evidenced.
4. Confirm the result is `unverifiable` with a clear explanation and no unsupported provenance.

## Validation Command

Run the Stage 5 focused test suite:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_provenance_chain.py tests/unit/test_query_result_schema.py tests/unit/test_fact_table_extractor.py tests/unit/test_pageindex_navigate_tool.py tests/unit/test_semantic_search_tool.py tests/unit/test_query_answer_formatting.py tests/unit/test_structured_query_tool.py tests/unit/test_fact_table_extractor_rows.py tests/unit/test_audit_mode.py tests/unit/test_query_agent_routing.py tests/integration/test_query_agent_grounded_answer.py tests/integration/test_query_agent_section_first.py tests/integration/test_query_agent_structured_fact.py tests/integration/test_query_agent_mixed_retrieval.py tests/integration/test_query_agent_audit_mode.py tests/integration/test_query_agent_real_infrastructure.py -q --basetemp=.test_tmp/pytest-stage5
```
