"""LangGraph assembly for Stage 1, Stage 2 extraction, and Stage 3 chunking."""

from __future__ import annotations

from src.agents.chunker import SemanticChunkingAgent
from src.agents.extractor import ExtractionRouter
from src.agents.triage import TriageAgent
from src.models.graph_state import GraphState


def build_graph(
    agent: TriageAgent | None = None,
    extractor: ExtractionRouter | None = None,
    chunker: SemanticChunkingAgent | None = None,
):
    """Build and compile graph with triage -> extract -> chunk flow."""
    from langgraph.graph import StateGraph

    triage_agent = agent or TriageAgent()
    extraction_router = extractor or ExtractionRouter()
    chunking_agent = chunker or SemanticChunkingAgent()
    graph = StateGraph(GraphState)
    graph.add_node("triage", triage_agent.triage_node)
    graph.add_node("extract", extraction_router.extract_node)
    graph.add_node("chunk", chunking_agent.chunk_node)
    graph.set_entry_point("triage")
    graph.add_edge("triage", "extract")
    graph.add_edge("extract", "chunk")
    graph.set_finish_point("chunk")
    return graph.compile()

