from src.indexing.pageindex_builder import PageIndexBuilder
from tests.unit._stage4_test_utils import make_ldus


def test_pageindex_builder_constructs_hierarchy():
    builder = PageIndexBuilder({"pageindex": {"artifact_dir": ".refinery/pageindex", "rule_version": "pageindex-test"}})
    document = builder.build_document("doc-1", make_ldus())
    assert document.section_count == 2
    assert len(document.root_sections) == 1
    root = document.root_sections[0]
    assert root.title == "1 Overview"
    assert root.child_sections[0].title == "1.1 Financial Results"
    assert root.child_sections[0].parent_section_id == root.id
