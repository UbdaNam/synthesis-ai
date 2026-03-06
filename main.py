from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.graph import build_graph
from src.models.graph_state import GraphState


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage 1 triage graph on a PDF.")
    parser.add_argument("file_path", nargs="?", default="sample_files/background-checks.pdf")
    parser.add_argument("--doc-id", default="background-checks")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    sample_pdf = Path(args.file_path)
    if not sample_pdf.exists():
        print(f"Sample PDF not found: {sample_pdf}")
        return

    graph = build_graph()
    raw_output = graph.invoke(GraphState(doc_id=args.doc_id, file_path=str(sample_pdf)))
    out = GraphState.model_validate(raw_output)
    if out.document_profile is None:
        print("No document profile generated.")
        return
    print(out.document_profile.model_dump(mode="json"))


if __name__ == "__main__":
    main()
