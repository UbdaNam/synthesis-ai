from __future__ import annotations

from dataclasses import dataclass

from .config import LANGUAGE_CONFIDENCE_FALLBACK


@dataclass(frozen=True)
class LanguageDetectionResult:
    code: str
    confidence: float


class LanguageDetector:
    """Lightweight deterministic language detector."""

    def detect(self, text: str) -> LanguageDetectionResult:
        normalized = (text or "").strip()
        if not normalized:
            return LanguageDetectionResult(code="und", confidence=LANGUAGE_CONFIDENCE_FALLBACK)

        try:
            from langdetect import DetectorFactory, detect_langs

            DetectorFactory.seed = 0
            candidates = detect_langs(normalized)
            if candidates:
                top = candidates[0]
                confidence = min(max(float(top.prob), 0.0), 1.0)
                return LanguageDetectionResult(code=top.lang, confidence=confidence)
        except Exception:
            pass

        # Safe fallback remains deterministic if model/package is unavailable.
        if all(ord(c) < 128 for c in normalized):
            return LanguageDetectionResult(code="en", confidence=LANGUAGE_CONFIDENCE_FALLBACK)
        return LanguageDetectionResult(code="und", confidence=LANGUAGE_CONFIDENCE_FALLBACK)

