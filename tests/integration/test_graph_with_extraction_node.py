from src.graph.graph import build_graph
from src.models.graph_state import GraphState


def test_graph_with_extraction_node(stage2_sample_pdf):
    graph = build_graph()
    out = GraphState.model_validate(graph.invoke(GraphState(doc_id="doc-graph", file_path=str(stage2_sample_pdf))))
    assert out.document_profile is not None
    assert out.extracted_document is not None or out.extraction_error is not None
