from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def test_main_runs_graph_and_prints_profile():
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "sample_files/background-checks.pdf"
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "main.py"),
            str(sample_pdf),
            "--doc-id",
            "doc-main-test",
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    profile = ast.literal_eval(lines[-1])
    assert profile["doc_id"] == "doc-main-test"
    assert "origin_type" in profile
    assert "estimated_extraction_cost" in profile
