from src.models.provenance_chain import ProvenanceChainItem
from tests.unit._stage5_test_utils import make_query_agent


def test_query_answer_formatting_maps_evidence_to_provenance(workspace_tmp):
    agent, state, _ = make_query_agent(workspace_tmp)
    result = agent.query(state, state.query_request.model_copy(update={}) if state.query_request else __import__('src.models.query_result', fromlist=['QueryRequest']).QueryRequest(doc_id=state.doc_id, user_query='What does the report say about financial results?'))
    assert result.provenance_chain
    assert isinstance(result.provenance_chain[0], ProvenanceChainItem)
