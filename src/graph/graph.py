"""LangGraph assembly for Stage 1 + Stage 2 extraction."""

from __future__ import annotations

from src.agents.extractor import ExtractionRouter
from src.agents.triage import TriageAgent
from src.models.graph_state import GraphState


def build_graph(agent: TriageAgent | None = None, extractor: ExtractionRouter | None = None):
    """Build and compile graph with triage -> extract flow."""
    from langgraph.graph import StateGraph

    triage_agent = agent or TriageAgent()
    extraction_router = extractor or ExtractionRouter()
    graph = StateGraph(GraphState)
    graph.add_node("triage", triage_agent.triage_node)
    graph.add_node("extract", extraction_router.extract_node)
    graph.set_entry_point("triage")
    graph.add_edge("triage", "extract")
    graph.set_finish_point("extract")
    return graph.compile()

