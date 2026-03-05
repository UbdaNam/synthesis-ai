from __future__ import annotations

from .config import (
    NATIVE_CHAR_DENSITY_THRESHOLD,
    NATIVE_IMAGE_RATIO_MAX,
    SCANNED_CHAR_COUNT_MAX,
    SCANNED_IMAGE_RATIO_MIN,
)
from .pdf_stats_analyzer import PDFStats
from models.document_profile import OriginType


class OriginClassifier:
    def classify(self, stats: PDFStats) -> OriginType:
        if stats.has_acroform:
            return OriginType.FORM_FILLABLE

        if (
            stats.median_character_density >= NATIVE_CHAR_DENSITY_THRESHOLD
            and stats.median_image_ratio <= NATIVE_IMAGE_RATIO_MAX
        ):
            return OriginType.NATIVE_DIGITAL

        if (
            stats.median_char_count <= SCANNED_CHAR_COUNT_MAX
            and stats.median_image_ratio >= SCANNED_IMAGE_RATIO_MIN
        ):
            return OriginType.SCANNED_IMAGE

        return OriginType.MIXED

