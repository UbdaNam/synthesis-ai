from pydantic import ValidationError

from src.models.page_index import PageIndexDocument, PageIndexNode


def test_page_index_node_schema_accepts_required_fields():
    node = PageIndexNode(
        id="section-1",
        doc_id="doc-1",
        title="1 Overview",
        page_start=1,
        page_end=2,
        child_sections=[],
        key_entities=[],
        summary="This section introduces the document. It provides scope and context.",
        data_types_present=["narrative_text"],
        chunk_ids=["chunk-1"],
        metadata={},
    )
    document = PageIndexDocument(
        doc_id="doc-1",
        root_sections=[node],
        section_count=1,
        chunk_count=1,
        artifact_path=".refinery/pageindex/doc-1.json",
        rule_version="pageindex-v1",
    )
    assert document.section_count == 1


def test_page_index_node_rejects_invalid_page_range():
    try:
        PageIndexNode(
            id="section-1",
            doc_id="doc-1",
            title="Broken",
            page_start=3,
            page_end=2,
            summary="This summary has two sentences. It remains valid otherwise.",
            data_types_present=[],
        )
    except ValidationError:
        pass
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected ValidationError for invalid page range")
