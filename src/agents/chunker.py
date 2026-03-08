"""Stage 3 Semantic Chunking Engine entrypoint."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from src.chunking.engine import ChunkingEngine
from src.chunking.validator import ChunkValidationError, ChunkValidator
from src.models.graph_state import GraphState


def _load_rules(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as stream:
        loaded = yaml.safe_load(stream) or {}
    if "chunking" not in loaded:
        loaded["chunking"] = {}
    return loaded


class SemanticChunkingAgent:
    """Public Stage 3 entrypoint for chunking and validation."""

    def __init__(
        self,
        config_path: str = "rubric/extraction_rules.yaml",
        validator: ChunkValidator | None = None,
        engine: ChunkingEngine | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self.config_path = config_path
        self.rules = _load_rules(config_path)
        self.validator = validator or ChunkValidator()
        self.engine = engine or ChunkingEngine(self.rules)
        self.timer = timer or time.perf_counter

    def _rule_version(self) -> str:
        return str(self.rules.get("chunking", {}).get("rule_version", "chunking-v1"))

    def _ledger_path(self) -> Path:
        raw = str(
            self.rules.get("chunking", {}).get(
                "chunking_ledger_path", ".refinery/chunking_ledger.jsonl"
            )
        )
        return Path(raw)

    def _append_ledger(self, payload: dict[str, Any]) -> None:
        path = self._ledger_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True))
            stream.write("\n")

    def chunk_node(self, state: GraphState) -> GraphState:
        if state.extracted_document is None:
            return state.model_copy(
                update={
                    "chunked_document": [],
                    "chunk_relationships": [],
                    "chunking_error": "missing_extracted_document",
                    "chunking_meta": {"rule_version": self._rule_version()},
                }
            )

        started = self.timer()
        try:
            chunks = self.engine.chunk_document(state.extracted_document)
            validated = self.validator.validate(chunks)
        except ChunkValidationError as exc:
            elapsed = max(0.0, self.timer() - started)
            meta = {
                "rule_version": self._rule_version(),
                "validation_status": "failed_closed",
                "processing_time": elapsed,
                "chunk_count": 0,
                "relationship_count": 0,
            }
            self._append_ledger(
                {
                    "doc_id": state.doc_id,
                    "rule_version": self._rule_version(),
                    "validation_status": "failed_closed",
                    "processing_time": elapsed,
                    "chunk_count": 0,
                    "relationship_count": 0,
                    "error_reason": str(exc),
                }
            )
            return state.model_copy(
                update={
                    "chunked_document": [],
                    "chunk_relationships": [],
                    "chunking_error": str(exc),
                    "chunking_meta": meta,
                }
            )

        elapsed = max(0.0, self.timer() - started)
        relationship_count = sum(len(chunk.relationships) for chunk in validated)
        relationships = [relationship for chunk in validated for relationship in chunk.relationships]
        meta = {
            "rule_version": self._rule_version(),
            "validation_status": "validated",
            "processing_time": elapsed,
            "chunk_count": len(validated),
            "relationship_count": relationship_count,
            "ledger_path": str(self._ledger_path()),
        }
        self._append_ledger(
            {
                "doc_id": state.doc_id,
                "rule_version": self._rule_version(),
                "validation_status": "validated",
                "processing_time": elapsed,
                "chunk_count": len(validated),
                "relationship_count": relationship_count,
            }
        )
        return state.model_copy(
            update={
                "chunked_document": validated,
                "chunk_relationships": relationships,
                "chunking_error": None,
                "chunking_meta": meta,
            }
        )
