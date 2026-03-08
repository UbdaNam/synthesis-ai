from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.env import ensure_env_loaded
from src.agents.query_agent import QueryAgent
from src.graph.graph import build_graph
from src.models.graph_state import GraphState
from src.models.query_result import QueryRequest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the document pipeline and optional Stage 5 query flow on a PDF.")
    parser.add_argument("file_path", nargs="?", default="sample_files/background-checks.pdf")
    parser.add_argument("--doc-id", default="background-checks")
    parser.add_argument("--query", help="Run a Stage 5 grounded question after the document pipeline finishes.")
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Interpret --query as an audit-mode claim verification request.",
    )
    return parser


def main() -> None:
    ensure_env_loaded()
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
    print({"extraction_error": out.extraction_error, "query_error": out.query_error})
    print(
        {
            "extraction_attempts": [
                attempt.model_dump(mode="json") for attempt in out.extraction_attempts
            ]
        }
    )
    if len(out.chunk_relationships) > 1:
        print(out.chunk_relationships[1].model_dump(mode="json"))
    if out.indexing_error:
        print({"index_error": out.indexing_error})
    if args.query:
        query_agent = QueryAgent()
        request = QueryRequest(
            doc_id=out.doc_id,
            user_query=args.query,
            mode="audit" if args.audit else "question_answering",
        )
        try:
            query_result = query_agent.query(out, request)
        except Exception as exc:  # pragma: no cover - runtime path
            print({"query_error": str(exc)})
            return
        print(
            {
                "query_result": query_result.model_dump(mode="json"),
            }
        )


if __name__ == "__main__":
    main()
