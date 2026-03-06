"""Stage 1 triage agent implementation."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import pdfplumber
import yaml
from langdetect import DetectorFactory, detect_langs
from pydantic import BaseModel, ConfigDict, Field

from src.models.document_profile import (
    DocumentProfile,
    DomainHint,
    EstimatedExtractionCost,
    LanguageSignal,
    LayoutComplexity,
    OriginType,
)
from src.models.graph_state import GraphState

DetectorFactory.seed = 0

ADVANCED_PROCESSING_COSTS = {"needs_layout_model", "needs_vision_model"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert incoming value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def _cluster_1d(points: list[float], threshold: float) -> int:
    """Simple deterministic clustering by sorted gap threshold."""
    if not points:
        return 0
    sorted_points = sorted(points)
    clusters = 1
    anchor = sorted_points[0]
    for point in sorted_points[1:]:
        if abs(point - anchor) > threshold:
            clusters += 1
            anchor = point
    return clusters


@dataclass(slots=True)
class PDFStatsSummary:
    """Aggregated deterministic per-document profiling signals."""

    total_pages: int
    total_characters: int
    avg_char_density: float
    avg_image_ratio: float
    font_metadata_presence: bool
    max_x_clusters: int
    table_grid_score: float
    figure_ratio: float
    extracted_text: str
    layout_signals_used: dict[str, float]
    acroform_present: bool
    column_balance_score: float = 0.0
    table_candidate_ratio: float = 0.0
    edge_density_score: float = 0.0


class ProfilingEvidenceEntry(BaseModel):
    """Required Stage 1 profiling evidence schema."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    character_density: float = Field(ge=0.0)
    image_ratio: float = Field(ge=0.0, le=1.0)
    font_metadata_presence: bool
    layout_signals_used: dict[str, float]
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language_code: str
    language_confidence: float = Field(ge=0.0, le=1.0)
    domain_hint: DomainHint
    estimated_extraction_cost: EstimatedExtractionCost
    processing_time: float = Field(ge=0.0)
    threshold_rule_reference: str = Field(min_length=1)


@runtime_checkable
class DomainClassifierStrategy(Protocol):
    """Pluggable domain classifier interface."""

    def classify(self, text: str) -> DomainHint:
        """Classify a document domain from extracted text."""


class KeywordDomainClassifier:
    """Default keyword scoring domain classifier."""

    def __init__(self, keyword_map: dict[str, list[str]]) -> None:
        self.keyword_map = {
            domain: [kw.lower() for kw in keywords]
            for domain, keywords in keyword_map.items()
        }

    def classify(self, text: str) -> DomainHint:
        tokens = _normalize_text(text)
        if not tokens:
            return "general"
        scores: dict[str, int] = {}
        for domain, keywords in self.keyword_map.items():
            score = sum(tokens.count(keyword) for keyword in keywords)
            scores[domain] = score
        best_domain = max(scores, key=scores.get)
        if scores.get(best_domain, 0) <= 0:
            return "general"
        if best_domain not in {"financial", "legal", "technical", "medical"}:
            return "general"
        return best_domain  # type: ignore[return-value]


class PDFStatsAnalyzer:
    """Compute deterministic PDF statistics with pdfplumber."""

    def analyze(self, file_path: str) -> PDFStatsSummary:
        with pdfplumber.open(file_path) as pdf:
            pages = list(pdf.pages)
            total_pages = len(pages)
            if total_pages == 0:
                return PDFStatsSummary(
                    total_pages=0,
                    total_characters=0,
                    avg_char_density=0.0,
                    avg_image_ratio=0.0,
                    font_metadata_presence=False,
                    max_x_clusters=0,
                    table_grid_score=0.0,
                    figure_ratio=0.0,
                    extracted_text="",
                    layout_signals_used={},
                    acroform_present=False,
                )

            char_counts: list[int] = []
            char_densities: list[float] = []
            image_ratios: list[float] = []
            font_presence: list[bool] = []
            cluster_counts: list[int] = []
            grid_scores: list[float] = []
            column_balance_scores: list[float] = []
            table_candidate_scores: list[float] = []
            edge_density_scores: list[float] = []
            extracted_text_parts: list[str] = []

            for page in pages:
                page_width = max(_safe_float(getattr(page, "width", 0.0), 0.0), 1.0)
                page_height = max(_safe_float(getattr(page, "height", 0.0), 0.0), 1.0)
                page_area = page_width * page_height

                chars = list(getattr(page, "chars", []) or [])
                images = list(getattr(page, "images", []) or [])
                words = list(
                    page.extract_words(
                        x_tolerance=2,
                        y_tolerance=2,
                        keep_blank_chars=False,
                        use_text_flow=True,
                    )
                    or []
                )

                char_count = len(chars)
                char_counts.append(char_count)
                char_density = char_count / page_area
                char_densities.append(char_density)
                font_presence.append(any(bool(c.get("fontname")) for c in chars))

                image_area = 0.0
                for image in images:
                    x0 = _safe_float(image.get("x0"))
                    x1 = _safe_float(image.get("x1"))
                    top = _safe_float(image.get("top"))
                    bottom = _safe_float(image.get("bottom"))
                    width = max(0.0, abs(x1 - x0))
                    height = max(0.0, abs(bottom - top))
                    image_area += width * height
                image_ratio = min(1.0, image_area / page_area)
                image_ratios.append(image_ratio)

                x_centers = [
                    (_safe_float(word.get("x0")) + _safe_float(word.get("x1"))) / 2.0
                    for word in words
                ]
                cluster_counts.append(_cluster_1d(x_centers, threshold=page_width * 0.12))

                # Column balance: left/right text bands with low gutter occupancy.
                if words:
                    page_mid = page_width / 2.0
                    gutter_min = page_width * 0.4
                    gutter_max = page_width * 0.6
                    left = sum(1 for x in x_centers if x < page_mid)
                    right = sum(1 for x in x_centers if x >= page_mid)
                    gutter = sum(1 for x in x_centers if gutter_min <= x <= gutter_max)
                    total = max(1, len(x_centers))
                    left_ratio = left / total
                    right_ratio = right / total
                    gutter_ratio = gutter / total
                    if left_ratio >= 0.25 and right_ratio >= 0.25:
                        column_balance_scores.append(max(0.0, 1.0 - gutter_ratio * 2.0))
                    else:
                        column_balance_scores.append(0.0)
                else:
                    column_balance_scores.append(0.0)

                # Table-like alignment heuristic: repeated vertical boundaries.
                x0_bins = [int(_safe_float(word.get("x0")) / 10.0) for word in words]
                x1_bins = [int(_safe_float(word.get("x1")) / 10.0) for word in words]
                total_bins = len(x0_bins) + len(x1_bins)
                boundary_repeat_score = 0.0
                if total_bins > 0:
                    frequencies: dict[int, int] = {}
                    for bucket in x0_bins + x1_bins:
                        frequencies[bucket] = frequencies.get(bucket, 0) + 1
                    repeated = sum(1 for count in frequencies.values() if count > 2)
                    boundary_repeat_score = min(1.0, repeated / max(1, len(frequencies)))

                # Use pdfplumber table finder with line strategies for stronger table signals.
                table_candidates = page.find_tables(
                    table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "intersection_tolerance": 5,
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                    }
                )
                table_candidate_score = min(1.0, len(table_candidates) / 2.0)
                table_candidate_scores.append(table_candidate_score)

                # Edge density score captures grid-like line presence.
                edges = list(getattr(page, "edges", []) or [])
                vertical_edges = 0
                horizontal_edges = 0
                for edge in edges:
                    x0 = _safe_float(edge.get("x0"))
                    x1 = _safe_float(edge.get("x1"))
                    top = _safe_float(edge.get("top"))
                    bottom = _safe_float(edge.get("bottom"))
                    if abs(x1 - x0) <= 1.5 and abs(bottom - top) > 5:
                        vertical_edges += 1
                    if abs(bottom - top) <= 1.5 and abs(x1 - x0) > 5:
                        horizontal_edges += 1
                min_cross_axis = min(vertical_edges, horizontal_edges)
                edge_density_score = min(1.0, min_cross_axis / max(1, len(words) // 5 or 1))
                edge_density_scores.append(edge_density_score)

                # Weighted deterministic table grid score.
                grid_score = (
                    0.45 * boundary_repeat_score
                    + 0.30 * edge_density_score
                    + 0.25 * table_candidate_score
                )
                grid_scores.append(grid_score)

                extracted_text_parts.append(page.extract_text() or "")

            acroform_present = bool(
                (
                    getattr(pdf, "doc", None)
                    and getattr(pdf.doc, "catalog", None)
                    and "AcroForm" in pdf.doc.catalog
                )
            )

            layout_signals = {
                "max_x_clusters": float(max(cluster_counts) if cluster_counts else 0),
                "table_grid_score": float(sum(grid_scores) / total_pages),
                "figure_ratio": float(sum(image_ratios) / total_pages),
                "column_balance_score": float(sum(column_balance_scores) / total_pages),
                "table_candidate_ratio": float(sum(table_candidate_scores) / total_pages),
                "edge_density_score": float(sum(edge_density_scores) / total_pages),
            }
            return PDFStatsSummary(
                total_pages=total_pages,
                total_characters=sum(char_counts),
                avg_char_density=float(sum(char_densities) / total_pages),
                avg_image_ratio=float(sum(image_ratios) / total_pages),
                font_metadata_presence=any(font_presence),
                max_x_clusters=max(cluster_counts) if cluster_counts else 0,
                table_grid_score=float(sum(grid_scores) / total_pages),
                figure_ratio=float(sum(image_ratios) / total_pages),
                extracted_text="\n".join(extracted_text_parts),
                layout_signals_used=layout_signals,
                acroform_present=acroform_present,
                column_balance_score=float(sum(column_balance_scores) / total_pages),
                table_candidate_ratio=float(sum(table_candidate_scores) / total_pages),
                edge_density_score=float(sum(edge_density_scores) / total_pages),
            )


class OriginClassifier:
    """Deterministic origin type classifier."""

    def classify(self, summary: PDFStatsSummary, config: dict[str, Any]) -> OriginType:
        thresholds = config["triage"]["origin_thresholds"]
        if summary.acroform_present:
            return "form_fillable"

        avg_chars_per_page = (
            summary.total_characters / summary.total_pages if summary.total_pages else 0.0
        )
        is_native = (
            summary.avg_char_density >= thresholds["native_char_density_min"]
            and summary.avg_image_ratio <= thresholds["native_image_ratio_max"]
            and summary.font_metadata_presence
        )
        is_scanned = (
            avg_chars_per_page <= thresholds["scanned_char_count_max"]
            and summary.avg_image_ratio >= thresholds["scanned_image_ratio_min"]
        )

        if is_native and not is_scanned:
            return "native_digital"
        if is_scanned and not is_native:
            return "scanned_image"
        if is_native and is_scanned:
            return "mixed"
        if summary.avg_image_ratio > 0.30 and summary.avg_char_density > 0.0005:
            return "mixed"
        if summary.avg_char_density <= 0.0003:
            return "scanned_image"
        return "native_digital"


class LayoutClassifier:
    """Deterministic layout complexity classifier."""

    def classify(self, summary: PDFStatsSummary, config: dict[str, Any]) -> LayoutComplexity:
        thresholds = config["triage"]["layout_thresholds"]
        column_balance_score = summary.layout_signals_used.get("column_balance_score", 0.0)
        multi_column = (
            summary.max_x_clusters >= thresholds["multi_column_x_clusters_min"]
            or column_balance_score >= 0.55
        )
        table_heavy = summary.table_grid_score >= thresholds["table_grid_score_min"]
        figure_heavy = (
            summary.avg_image_ratio >= thresholds["figure_heavy_image_ratio_min"]
        )
        triggered = sum([multi_column, table_heavy, figure_heavy])
        if triggered > 1:
            return "mixed"
        if table_heavy:
            return "table_heavy"
        if figure_heavy:
            return "figure_heavy"
        if multi_column:
            return "multi_column"
        return "single_column"


class ExtractionCostResolver:
    """Deterministically map profile fields to extraction cost class."""

    def resolve(
        self, origin_type: OriginType, layout_complexity: LayoutComplexity
    ) -> EstimatedExtractionCost:
        if origin_type == "scanned_image" or layout_complexity == "figure_heavy":
            return "needs_vision_model"
        if origin_type in {"mixed", "form_fillable"} or layout_complexity in {
            "multi_column",
            "table_heavy",
            "mixed",
        }:
            return "needs_layout_model"
        return "fast_text_sufficient"


def requires_advanced_processing(cost: EstimatedExtractionCost) -> bool:
    """SC-004 rule for advanced processing."""
    return cost in ADVANCED_PROCESSING_COSTS


def _load_config(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as stream:
        parsed = yaml.safe_load(stream) or {}
    if "triage" not in parsed:
        raise ValueError("Missing `triage` section in extraction_rules.yaml")
    return parsed


class TriageAgent:
    """Stage 1 triage orchestrator."""

    def __init__(
        self,
        config_path: str = "rubric/extraction_rules.yaml",
        profiles_dir: str = ".refinery/profiles",
        profiling_ledger_path: str = ".refinery/profiling_ledger.jsonl",
        analyzer: PDFStatsAnalyzer | None = None,
        origin_classifier: OriginClassifier | None = None,
        layout_classifier: LayoutClassifier | None = None,
        cost_resolver: ExtractionCostResolver | None = None,
        domain_classifier: DomainClassifierStrategy | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self.config_path = config_path
        self.config = _load_config(config_path)
        self.profiles_dir = Path(profiles_dir)
        self.profiling_ledger_path = Path(profiling_ledger_path)
        self.analyzer = analyzer or PDFStatsAnalyzer()
        self.origin_classifier = origin_classifier or OriginClassifier()
        self.layout_classifier = layout_classifier or LayoutClassifier()
        self.cost_resolver = cost_resolver or ExtractionCostResolver()
        keyword_map = self.config["triage"].get("domain_keywords", {})
        self.domain_classifier = domain_classifier or KeywordDomainClassifier(keyword_map)
        self.timer = timer or time.perf_counter

    def detect_language(self, text: str) -> LanguageSignal:
        language_config = self.config["triage"]["language"]
        fallback_code = language_config["fallback_code"]
        fallback_confidence = language_config["fallback_confidence"]
        if not text or not text.strip():
            return LanguageSignal(code=fallback_code, confidence=fallback_confidence)
        try:
            result = detect_langs(text)
            if not result:
                return LanguageSignal(code=fallback_code, confidence=fallback_confidence)
            best = max(result, key=lambda item: item.prob)
            return LanguageSignal(code=str(best.lang), confidence=float(best.prob))
        except Exception:
            return LanguageSignal(code=fallback_code, confidence=fallback_confidence)

    def profile_document(self, doc_id: str, file_path: str) -> tuple[DocumentProfile, PDFStatsSummary]:
        summary = self.analyzer.analyze(file_path)
        origin_type = self.origin_classifier.classify(summary, self.config)
        layout_complexity = self.layout_classifier.classify(summary, self.config)
        language = self.detect_language(summary.extracted_text)
        domain_hint = self.domain_classifier.classify(summary.extracted_text)
        estimated_extraction_cost = self.cost_resolver.resolve(origin_type, layout_complexity)
        profile = DocumentProfile(
            doc_id=doc_id,
            origin_type=origin_type,
            layout_complexity=layout_complexity,
            language=language,
            domain_hint=domain_hint,
            estimated_extraction_cost=estimated_extraction_cost,
            deterministic_version=self.config["triage"]["deterministic_version"],
        )
        return profile, summary

    def persist_profile(self, profile: DocumentProfile) -> Path:
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        target = self.profiles_dir / f"{profile.doc_id}.json"
        payload = profile.model_dump(mode="json")
        with open(target, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        return target

    def write_profiling_evidence(self, entry: ProfilingEvidenceEntry) -> Path:
        self.profiling_ledger_path.parent.mkdir(parents=True, exist_ok=True)
        payload = entry.model_dump(mode="json")
        with open(self.profiling_ledger_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True))
            stream.write("\n")
        return self.profiling_ledger_path

    def triage_node(self, state: GraphState) -> GraphState:
        started_at = self.timer()
        profile, summary = self.profile_document(state.doc_id, state.file_path)
        self.persist_profile(profile)
        processing_time = max(0.0, self.timer() - started_at)
        evidence = ProfilingEvidenceEntry(
            doc_id=state.doc_id,
            character_density=summary.avg_char_density,
            image_ratio=summary.avg_image_ratio,
            font_metadata_presence=summary.font_metadata_presence,
            layout_signals_used=summary.layout_signals_used,
            origin_type=profile.origin_type,
            layout_complexity=profile.layout_complexity,
            language_code=profile.language.code,
            language_confidence=profile.language.confidence,
            domain_hint=profile.domain_hint,
            estimated_extraction_cost=profile.estimated_extraction_cost,
            processing_time=processing_time,
            threshold_rule_reference=self.config["triage"]["deterministic_version"],
        )
        self.write_profiling_evidence(evidence)
        return GraphState(
            doc_id=state.doc_id,
            file_path=state.file_path,
            document_profile=profile,
        )

