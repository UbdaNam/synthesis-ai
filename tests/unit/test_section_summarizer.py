from src.indexing.section_summarizer import SectionSummarizer
from tests.unit._stage4_test_utils import FakeLLM, make_ldus


def test_section_summarizer_shapes_request_and_validates_output():
    summarizer = SectionSummarizer(
        rules={
            "pageindex": {
                "max_chunks_per_summary_request": 2,
                "summary_model_name": "openai/gpt-4o-mini",
            }
        },
        llm_factory=FakeLLM,
    )
    request = summarizer.build_request("doc-1", "section-1", "1 Overview", make_ldus())
    assert len(request.chunk_ids) == 2
    result = summarizer.summarize_section(request)
    assert result.summary.count(".") >= 2
    assert set(result.source_chunk_ids).issubset(set(request.chunk_ids))
