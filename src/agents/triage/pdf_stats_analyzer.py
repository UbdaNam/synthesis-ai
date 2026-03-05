from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Any

import pdfplumber


@dataclass(frozen=True)
class PDFStats:
    character_count_per_page: list[int]
    character_density: list[float]
    image_area_ratio: list[float]
    font_metadata_presence: list[bool]
    bounding_box_distribution: dict[str, float]
    has_acroform: bool
    extracted_text: str

    @property
    def median_character_density(self) -> float:
        return median(self.character_density) if self.character_density else 0.0

    @property
    def median_image_ratio(self) -> float:
        return median(self.image_area_ratio) if self.image_area_ratio else 0.0

    @property
    def median_char_count(self) -> float:
        return median(self.character_count_per_page) if self.character_count_per_page else 0.0

    @property
    def page_count(self) -> int:
        return len(self.character_count_per_page)


class PDFStatsAnalyzer:
    """Computes deterministic page-level metrics using pdfplumber."""

    def analyze(self, file_path: str) -> PDFStats:
        with pdfplumber.open(file_path) as pdf:
            char_counts: list[int] = []
            densities: list[float] = []
            image_ratios: list[float] = []
            font_presence: list[bool] = []
            text_parts: list[str] = []
            x_positions: list[float] = []
            y_positions: list[float] = []

            has_acroform = self._has_acroform(pdf)
            for page in pdf.pages:
                page_area = max(float(page.width) * float(page.height), 1.0)
                chars = page.chars or []
                words = page.extract_words() or []
                images = page.images or []

                char_count = len(chars)
                char_counts.append(char_count)
                densities.append(char_count / page_area)
                font_presence.append(
                    any(bool(c.get("fontname")) and c.get("size") is not None for c in chars)
                )

                image_area = 0.0
                for image in images:
                    image_area += max(float(image.get("width", 0.0)), 0.0) * max(
                        float(image.get("height", 0.0)), 0.0
                    )
                image_ratios.append(min(max(image_area / page_area, 0.0), 1.0))

                for word in words:
                    x_positions.append(float(word.get("x0", 0.0)))
                    y_positions.append(float(word.get("top", 0.0)))

                text_parts.append(page.extract_text() or "")

            bbox_distribution = self._bbox_distribution(x_positions, y_positions)
            return PDFStats(
                character_count_per_page=char_counts,
                character_density=densities,
                image_area_ratio=image_ratios,
                font_metadata_presence=font_presence,
                bounding_box_distribution=bbox_distribution,
                has_acroform=has_acroform,
                extracted_text="\n".join(text_parts).strip(),
            )

    @staticmethod
    def _has_acroform(pdf: Any) -> bool:
        catalog = getattr(getattr(pdf, "doc", None), "catalog", None)
        return bool(catalog and catalog.get("AcroForm"))

    @staticmethod
    def _bbox_distribution(x_positions: list[float], y_positions: list[float]) -> dict[str, float]:
        if not x_positions or not y_positions:
            return {"x_cluster_count": 1.0, "grid_alignment_score": 0.0}

        x_clusters = 1
        sorted_x = sorted(x_positions)
        for i in range(1, len(sorted_x)):
            if sorted_x[i] - sorted_x[i - 1] > 90.0:
                x_clusters += 1

        x_bucket: dict[int, int] = {}
        y_bucket: dict[int, int] = {}
        for x in x_positions:
            x_bucket[round(x / 8)] = x_bucket.get(round(x / 8), 0) + 1
        for y in y_positions:
            y_bucket[round(y / 6)] = y_bucket.get(round(y / 6), 0) + 1

        repeated_x = sum(1 for v in x_bucket.values() if v >= 4)
        repeated_y = sum(1 for v in y_bucket.values() if v >= 4)
        grid_alignment_score = min((repeated_x * repeated_y) / 100.0, 1.0)
        return {
            "x_cluster_count": float(max(1, x_clusters)),
            "grid_alignment_score": float(grid_alignment_score),
        }

