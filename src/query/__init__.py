"""Stage 5 query utilities and artifact helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from src.config.env import ensure_env_loaded
from src.models.ldu import LDU


DEFAULT_QUERY_ARTIFACT_DIR = ".refinery/query"
DEFAULT_LDU_CACHE_DIR = ".refinery/query/ldu_cache"
DEFAULT_FACTS_DB_PATH = ".refinery/query/facts.db"


class QueryStageError(RuntimeError):
    """Raised when Stage 5 query infrastructure fails closed."""



def load_rules(config_path: str = "rubric/extraction_rules.yaml") -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as stream:
        loaded = yaml.safe_load(stream) or {}
    if "query" not in loaded:
        loaded["query"] = {}
    return loaded


class QueryArtifactPaths:
    """Filesystem paths used by the Stage 5 query layer."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        config = (rules or {}).get("query", {})
        base_dir = Path(str(config.get("artifact_dir", DEFAULT_QUERY_ARTIFACT_DIR)))
        self.artifact_dir = base_dir
        self.ldu_cache_dir = Path(str(config.get("ldu_cache_dir", base_dir / "ldu_cache")))
        self.facts_db_path = Path(
            str(os.getenv("QUERY_FACTS_DB_PATH", config.get("facts_db_path", DEFAULT_FACTS_DB_PATH)))
        )

    def ensure(self) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.ldu_cache_dir.mkdir(parents=True, exist_ok=True)
        self.facts_db_path.parent.mkdir(parents=True, exist_ok=True)

    def ldu_cache_path(self, doc_id: str) -> Path:
        return self.ldu_cache_dir / f"{doc_id}.json"



def persist_ldu_cache(doc_id: str, chunks: list[LDU], rules: dict[str, Any] | None = None) -> Path:
    paths = QueryArtifactPaths(rules)
    paths.ensure()
    path = paths.ldu_cache_path(doc_id)
    payload = [chunk.model_dump(mode="json") for chunk in chunks]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path



def load_ldu_cache(doc_id: str, rules: dict[str, Any] | None = None) -> list[LDU]:
    path = QueryArtifactPaths(rules).ldu_cache_path(doc_id)
    if not path.exists():
        raise QueryStageError("missing_ldu_cache")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [LDU.model_validate(item) for item in payload]



def ensure_query_env_loaded() -> None:
    ensure_env_loaded()
