from __future__ import annotations

import json

from models.document_profile import DocumentProfile


def serialize_profile_deterministic(profile: DocumentProfile) -> str:
    return json.dumps(profile.model_dump(mode="json"), ensure_ascii=True, sort_keys=True, separators=(",", ":"))

