from __future__ import annotations

import json
from pathlib import Path

from ..models.document_profile import DocumentProfile


class ProfileRepository:
    def __init__(self, base_dir: str = ".refinery/profiles") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, profile: DocumentProfile) -> Path:
        path = self.base_dir / f"{profile.doc_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(profile.model_dump(mode="json"), f, ensure_ascii=True, sort_keys=True, indent=2)
            f.write("\n")
        return path

