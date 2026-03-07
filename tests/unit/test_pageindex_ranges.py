from src.indexing.pageindex_builder import PageIndexBuilder
from tests.unit._stage4_test_utils import make_ldus


def test_pageindex_builder_derives_page_ranges():
    builder = PageIndexBuilder({"pageindex": {"artifact_dir": ".refinery/pageindex", "rule_version": "pageindex-test"}})
    document = builder.build_document("doc-1", make_ldus())
    root = document.root_sections[0]
    child = root.child_sections[0]
    assert root.page_start == 1
    assert root.page_end == 3
    assert child.page_start == 2
    assert child.page_end == 3
