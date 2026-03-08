import pytest

from src.models.extracted_document import BoundingBox
from src.models.provenance_chain import ProvenanceChainItem
from src.models.query_result import QueryRequest, QueryResult


def test_query_result_requires_provenance_for_supported_answers():
    with pytest.raises(ValueError):
        QueryResult(answer="Supported answer", provenance_chain=[], support_status="supported", retrieval_path_used=["semantic_search"])


def test_query_request_defaults_to_question_answering():
    request = QueryRequest(doc_id="doc-1", user_query="What is revenue?")
    assert request.mode == "question_answering"


def test_query_result_accepts_supported_answer_with_provenance():
    result = QueryResult(
        answer="Revenue is USD 1250000.",
        provenance_chain=[
            ProvenanceChainItem(
                document_name="doc-1",
                page_number=2,
                bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                content_hash="hash-1",
                chunk_id="chunk-1",
            )
        ],
        support_status="supported",
        retrieval_path_used=["structured_query"],
    )
    assert result.support_status == "supported"
