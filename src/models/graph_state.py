"""Graph state contract for Stage 1 LangGraph entrypoint."""

from pydantic import BaseModel, ConfigDict, Field

from .document_profile import DocumentProfile


class GraphState(BaseModel):
    """Graph boundary type for triage stage."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    document_profile: DocumentProfile | None = None

