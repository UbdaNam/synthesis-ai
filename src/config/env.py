"""Environment loading utilities."""

from __future__ import annotations

from pathlib import Path

_LOADED = False


def ensure_env_loaded() -> None:
    """Load `.env` from project root once per process."""

    global _LOADED
    if _LOADED:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        # Allow runtime to proceed when python-dotenv is not installed.
        _LOADED = True
        return
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=project_root / ".env", override=False)
    _LOADED = True
