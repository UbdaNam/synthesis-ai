"""LangGraph assembly for Stage 1 triage."""

from __future__ import annotations

from src.agents.triage import TriageAgent
from src.models.graph_state import GraphState


def build_graph(agent: TriageAgent | None = None):
    """Build and compile the Stage 1 graph with triage as entrypoint."""
    from langgraph.graph import StateGraph

    triage_agent = agent or TriageAgent()
    graph = StateGraph(GraphState)
    graph.add_node("triage", triage_agent.triage_node)
    graph.set_entry_point("triage")
    graph.set_finish_point("triage")
    return graph.compile()

