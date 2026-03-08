"""Helpers for creating Chroma clients without leaking unrelated env vars."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

# Chroma's settings model eagerly consumes environment variables and rejects
# unrelated lowercase keys loaded from the repo's `.env`. Strip the known
# non-Chroma keys while importing/creating the client, then restore them.
_ENV_KEYS_TO_MASK = (
    "langsmith_tracing",
    "langsmith_endpoint",
    "langsmith_api_key",
    "langsmith_project",
    "openrouter_api_key",
    "openai_api_key",
    "pageindex_vector_persist_directory",
)


@contextmanager
def masked_chroma_environment() -> Iterator[None]:
    """Temporarily hide non-Chroma env keys that break Chroma settings."""

    removed: dict[str, str] = {}
    for key in _ENV_KEYS_TO_MASK:
        if key in os.environ:
            removed[key] = os.environ.pop(key)
    try:
        yield
    finally:
        os.environ.update(removed)


def create_persistent_client(path: str) -> Any:
    """Create a Chroma persistent client under a sanitized environment."""

    original_cwd = Path.cwd()
    isolated_cwd = Path(".test_tmp/chroma_env")
    isolated_cwd.mkdir(parents=True, exist_ok=True)
    with masked_chroma_environment():
        os.chdir(isolated_cwd)
        try:
            import chromadb

            return chromadb.PersistentClient(path=path)
        finally:
            os.chdir(original_cwd)
