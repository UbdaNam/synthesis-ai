from src.agents.indexer import PageIndexingAgent
from src.indexing.section_summarizer import SummaryGenerationError
from tests.unit._stage4_test_utils import make_graph_state


class FailingSummarizer:
    def build_request(self, *args, **kwargs):
        raise SummaryGenerationError("summary_generation_failed")


def test_indexer_fails_closed_on_summary_error(workspace_tmp):
    agent = PageIndexingAgent(
        config_path="rubric/extraction_rules.yaml",
        summarizer=FailingSummarizer(),
        timer=lambda: 100.0,
    )
    out = agent.index_node(make_graph_state())
    assert out.page_index is None
    assert out.indexing_error == "summary_generation_failed"
