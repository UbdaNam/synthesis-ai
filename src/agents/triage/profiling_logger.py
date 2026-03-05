from __future__ import annotations

import json
from pathlib import Path

from .profiling_ledger_schema import ProfilingLedgerEntry


class ProfilingLogger:
    def __init__(self, ledger_path: str = ".refinery/profiling_ledger.jsonl") -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: ProfilingLedgerEntry) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.model_dump(mode="json"), sort_keys=True))
            f.write("\n")

