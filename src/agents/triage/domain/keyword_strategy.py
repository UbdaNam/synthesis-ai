from __future__ import annotations

from src.models.document_profile import DomainHint


class KeywordDomainClassifier:
    KEYWORDS = {
        DomainHint.FINANCIAL: {"balance", "invoice", "revenue", "asset", "liability", "tax"},
        DomainHint.LEGAL: {"agreement", "clause", "party", "statute", "compliance", "contract"},
        DomainHint.TECHNICAL: {"architecture", "api", "system", "algorithm", "module", "protocol"},
        DomainHint.MEDICAL: {"patient", "diagnosis", "treatment", "clinical", "medicine", "symptom"},
    }

    def classify(self, text: str) -> DomainHint:
        lower = (text or "").lower()
        scores: dict[DomainHint, int] = {}
        for hint, words in self.KEYWORDS.items():
            scores[hint] = sum(lower.count(word) for word in words)
        best = max(scores.items(), key=lambda x: x[1]) if scores else (DomainHint.GENERAL, 0)
        return best[0] if best[1] > 0 else DomainHint.GENERAL

