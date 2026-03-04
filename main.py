from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from synthesis_ai.graph.triage_node import TriageNode
from synthesis_ai.models.graph_state import GraphState


def main() -> None:
    sample_pdf = Path("background-checks.pdf")
    if not sample_pdf.exists():
        print("Sample PDF not found. Provide a PDF and invoke TriageNode from your pipeline.")
        return
    node = TriageNode()
    out = node(GraphState(doc_id="background-checks", file_path=str(sample_pdf)))
    if out.document_profile is not None:
        print(out.document_profile.model_dump(mode="json"))
    else:
        print("No document profile generated.")


if __name__ == "__main__":
    main()
