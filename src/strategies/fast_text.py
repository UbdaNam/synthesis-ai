"""Strategy A: fast deterministic text extraction using pdfplumber."""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from src.models.extracted_document import BoundingBox, ExtractedDocument, TextBlock, stable_content_hash
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult


class FastTextExtractor(BaseExtractionStrategy):
    """Low-cost extractor for native, single-column PDFs."""

    name = "fast_text"

    def _signals(self, context: ExtractionContext) -> dict[str, float | bool]:
        char_count = 0
        char_density = 0.0
        image_to_page_ratio = 0.0
        font_metadata_presence = False
        page_count = 0

        with pdfplumber.open(context.file_path) as pdf:
            pages = list(pdf.pages)
            page_count = max(1, len(pages))
            page_areas: list[float] = []
            image_ratios: list[float] = []

            for page in pages:
                width = max(float(getattr(page, "width", 1.0)), 1.0)
                height = max(float(getattr(page, "height", 1.0)), 1.0)
                area = width * height
                page_areas.append(area)

                chars = list(getattr(page, "chars", []) or [])
                images = list(getattr(page, "images", []) or [])
                char_count += len(chars)
                if any(bool(char.get("fontname")) for char in chars):
                    font_metadata_presence = True

                image_area = 0.0
                for image in images:
                    x0 = float(image.get("x0", 0.0) or 0.0)
                    x1 = float(image.get("x1", 0.0) or 0.0)
                    top = float(image.get("top", 0.0) or 0.0)
                    bottom = float(image.get("bottom", 0.0) or 0.0)
                    image_area += max(0.0, abs(x1 - x0)) * max(0.0, abs(bottom - top))
                image_ratios.append(min(1.0, image_area / area))

            total_area = max(1.0, sum(page_areas))
            char_density = char_count / total_area
            image_to_page_ratio = float(sum(image_ratios) / page_count)

        return {
            "char_count": float(char_count),
            "char_density": char_density,
            "image_to_page_ratio": image_to_page_ratio,
            "font_metadata_presence": font_metadata_presence,
            "page_count": float(page_count),
        }

    def _confidence(self, signals: dict[str, float | bool], rules: dict) -> float:
        fast_rules = rules.get("extraction", {}).get("fast_text", {})
        signal_rules = fast_rules.get("confidence_signals", {})
        weights = fast_rules.get("weights", {})

        cc_min = float(signal_rules.get("char_count_min", 200))
        cd_min = float(signal_rules.get("char_density_min", 0.001))
        ir_max = float(signal_rules.get("image_ratio_max", 0.35))
        font_required = bool(signal_rules.get("font_metadata_required", False))

        w_cc = float(weights.get("char_count", 0.35))
        w_cd = float(weights.get("char_density", 0.35))
        w_ir = float(weights.get("image_to_page_ratio", 0.2))
        w_font = float(weights.get("font_metadata_presence", 0.1))

        char_count = float(signals["char_count"])
        char_density = float(signals["char_density"])
        image_ratio = float(signals["image_to_page_ratio"])
        font_presence = bool(signals["font_metadata_presence"])

        cc_score = min(1.0, char_count / cc_min) if cc_min > 0 else 1.0
        cd_score = min(1.0, char_density / cd_min) if cd_min > 0 else 1.0
        ir_score = 1.0 if image_ratio <= ir_max else max(0.0, 1.0 - (image_ratio - ir_max))
        font_score = 1.0 if (font_presence or not font_required) else 0.0

        return max(0.0, min(1.0, (w_cc * cc_score) + (w_cd * cd_score) + (w_ir * ir_score) + (w_font * font_score)))

    def _extract_blocks(self, context: ExtractionContext) -> tuple[list[TextBlock], int]:
        blocks: list[TextBlock] = []
        with pdfplumber.open(context.file_path) as pdf:
            pages = list(pdf.pages)
            for page_idx, page in enumerate(pages, start=1):
                words = page.extract_words(use_text_flow=True) or []
                for idx, word in enumerate(words):
                    text = str(word.get("text", "")).strip()
                    if not text:
                        continue
                    x0 = float(word.get("x0", 0.0) or 0.0)
                    x1 = float(word.get("x1", 0.0) or 0.0)
                    top = float(word.get("top", 0.0) or 0.0)
                    bottom = float(word.get("bottom", 0.0) or 0.0)
                    block_id = f"tb-{page_idx}-{idx}"
                    blocks.append(
                        TextBlock(
                            id=block_id,
                            page_number=page_idx,
                            bounding_box=BoundingBox(x0=x0, y0=top, x1=x1, y1=bottom),
                            reading_order=idx,
                            block_type="paragraph",
                            text=text,
                            content_hash=stable_content_hash(text),
                            confidence=1.0,
                        )
                    )
        return blocks, max(1, len(pages))

    def estimate_cost(self, rules: dict, page_count: int) -> float:
        costing = rules.get("extraction", {}).get("costing", {})
        base = float(costing.get("fast_text_base", 0.001))
        per_page = float(costing.get("fast_text_per_page", 0.0002))
        return base + (per_page * max(1, page_count))

    def extract(self, context: ExtractionContext) -> StrategyResult:
        if not Path(context.file_path).exists():
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=0.0,
                document=None,
                cost_estimate=0.0,
                error="file_not_found",
            )

        signals = self._signals(context)
        confidence = self._confidence(signals, context.rules)
        text_blocks, page_count = self._extract_blocks(context)
        if not text_blocks:
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=confidence,
                document=None,
                cost_estimate=self.estimate_cost(context.rules, page_count),
                metadata={"signals": signals, "page_count": page_count},
                error="no_text_blocks",
            )

        document = ExtractedDocument(
            doc_id=context.doc_id,
            strategy_used=self.name,
            confidence_score=confidence,
            metadata={"page_count": page_count, "signals": signals},
            text_blocks=text_blocks,
            tables=[],
            figures=[],
        )
        return StrategyResult(
            strategy_used=self.name,
            confidence_score=confidence,
            document=document,
            cost_estimate=self.estimate_cost(context.rules, page_count),
            metadata={"signals": signals, "page_count": page_count},
        )
