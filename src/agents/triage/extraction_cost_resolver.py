from __future__ import annotations

from models.document_profile import EstimatedExtractionCost, LayoutComplexity, OriginType


class ExtractionCostResolver:
    def resolve(
        self,
        origin_type: OriginType,
        layout_complexity: LayoutComplexity,
    ) -> EstimatedExtractionCost:
        if origin_type == OriginType.SCANNED_IMAGE:
            return EstimatedExtractionCost.NEEDS_VISION_MODEL
        if layout_complexity == LayoutComplexity.FIGURE_HEAVY:
            return EstimatedExtractionCost.NEEDS_VISION_MODEL
        if layout_complexity in {
            LayoutComplexity.MULTI_COLUMN,
            LayoutComplexity.TABLE_HEAVY,
            LayoutComplexity.MIXED,
        }:
            return EstimatedExtractionCost.NEEDS_LAYOUT_MODEL
        return EstimatedExtractionCost.FAST_TEXT_SUFFICIENT

