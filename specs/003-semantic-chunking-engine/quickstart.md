# Quickstart: Semantic Chunking Engine

## Scenario 1: Mixed-content document produces retrieval-ready LDUs

1. Start with a `GraphState` containing a valid `ExtractedDocument` from Stage 2.
2. Include:
   - heading blocks
   - narrative paragraph blocks
   - a numbered list
   - one structured table
   - one figure with caption
3. Run the Stage 3 chunker node.
4. Verify:
   - output is a typed `List[LDU]`
   - every LDU contains required fields
   - section context is propagated
   - table chunks preserve headers
   - figure chunks contain caption metadata
   - cross-references are stored as relationships

## Scenario 2: Oversized table is split safely

1. Create a Stage 2 `ExtractedDocument` with a table large enough to exceed the
   configured chunk token limit.
2. Run the Stage 3 chunker node.
3. Verify:
   - the table is split by row groups
   - every derived table chunk repeats the header context
   - validator accepts the emitted chunks

## Scenario 3: Oversized numbered list preserves continuity

1. Create consecutive `list_item` blocks under one heading whose combined token
   count exceeds the list split threshold.
2. Run the Stage 3 chunker node.
3. Verify:
   - Stage 3 emits multiple list-derived LDUs only after threshold enforcement
   - each derived chunk preserves list continuity metadata
   - each derived chunk retains the same parent section

## Scenario 4: Invalid upstream provenance fails closed

1. Create an `ExtractedDocument` where one content unit required for chunking is
   missing provenance needed by Stage 3.
2. Run the Stage 3 chunker node.
3. Verify:
   - no downstream-ready LDU list is published
   - Stage 3 returns a structured `chunking_error`
   - audit metadata records the validation failure
