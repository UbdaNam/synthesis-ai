from __future__ import annotations

from typing import Protocol

from ...models.document_profile import DomainHint


class DomainClassifierStrategy(Protocol):
    def classify(self, text: str) -> DomainHint:
        ...

