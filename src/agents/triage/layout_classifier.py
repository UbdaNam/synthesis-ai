from __future__ import annotations

from .config import FIGURE_HEAVY_IMAGE_RATIO_MIN, MULTI_COLUMN_CLUSTER_MIN, TABLE_HEAVY_GRID_SCORE_MIN
from .pdf_stats_analyzer import PDFStats
from models.document_profile import LayoutComplexity, OriginType


class LayoutClassifier:
    def classify(self, stats: PDFStats, origin_type: OriginType) -> LayoutComplexity:
        x_clusters = int(stats.bounding_box_distribution.get("x_cluster_count", 1))
        grid_score = float(stats.bounding_box_distribution.get("grid_alignment_score", 0.0))

        if stats.median_image_ratio >= FIGURE_HEAVY_IMAGE_RATIO_MIN and stats.median_char_count < 80:
            return LayoutComplexity.FIGURE_HEAVY
        if grid_score >= TABLE_HEAVY_GRID_SCORE_MIN:
            return LayoutComplexity.TABLE_HEAVY
        if x_clusters >= MULTI_COLUMN_CLUSTER_MIN:
            return LayoutComplexity.MULTI_COLUMN
        if origin_type == OriginType.MIXED:
            return LayoutComplexity.MIXED
        return LayoutComplexity.SINGLE_COLUMN

