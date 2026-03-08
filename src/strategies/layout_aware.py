"""Strategy B: layout-aware extraction using Docling or MinerU provider adapters."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from src.models.document_profile import DocumentProfile
from src.models.extracted_document import (
    BoundingBox,
    ExtractedDocument,
    FigureBlock,
    StructuredTable,
    TextBlock,
    stable_content_hash,
)
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult


class LayoutProvider(Protocol):
    """Provider contract for layout-aware extraction backends."""

    name: str

    def extract(self, file_path: str) -> dict[str, Any]:
        """Return provider-native structured payload."""


@dataclass(slots=True)
class DoclingLayoutProvider:
    """Docling-backed extraction provider."""

    name: str = "docling"
    provider_rules: dict[str, Any] | None = None
    document_profile: DocumentProfile | None = None

    def _docling_rules(self) -> dict[str, Any]:
        layout = self.provider_rules or {}
        providers = layout.get("providers", {}) if isinstance(layout, dict) else {}
        docling = providers.get("docling", {}) if isinstance(providers, dict) else {}
        return cast(dict[str, Any], docling if isinstance(docling, dict) else {})

    def _do_ocr(self) -> bool:
        cfg = self._docling_rules()
        profile = self.document_profile
        if profile is None:
            return bool(cfg.get("do_ocr_default", False))
        if profile.origin_type == "scanned_image":
            return bool(cfg.get("do_ocr_scanned", True))
        if profile.origin_type == "mixed":
            return bool(cfg.get("do_ocr_mixed", True))
        return bool(cfg.get("do_ocr_native_digital", False))

    def extract(self, file_path: str, force_ocr: bool = False) -> dict[str, Any]:
        try:
            from docling.datamodel.base_models import ConversionStatus, InputFormat  # type: ignore
            from docling.datamodel.pipeline_options import PdfPipelineOptions  # type: ignore
            from docling.document_converter import DocumentConverter, PdfFormatOption  # type: ignore
        except ImportError as exc:
            raise RuntimeError("docling provider is not installed") from exc

        cfg = self._docling_rules()
        max_pages = int(cfg.get("max_pages", 1000))
        max_file_size_mb = int(cfg.get("max_file_size_mb", 100))
        timeout_seconds = float(cfg.get("document_timeout_seconds", 180))
        do_ocr = bool(force_ocr or self._do_ocr())
        force_backend_text = bool(cfg.get("force_backend_text", True))

        pipeline = PdfPipelineOptions()
        pipeline.document_timeout = timeout_seconds
        pipeline.do_table_structure = bool(cfg.get("do_table_structure", True))
        pipeline.do_picture_description = bool(cfg.get("do_picture_description", False))
        pipeline.do_chart_extraction = bool(cfg.get("do_chart_extraction", False))
        pipeline.do_ocr = do_ocr
        pipeline.force_backend_text = force_backend_text and not do_ocr
        pipeline.generate_page_images = bool(cfg.get("generate_page_images", False))
        pipeline.generate_picture_images = bool(cfg.get("generate_picture_images", False))
        pipeline.generate_table_images = bool(cfg.get("generate_table_images", False))
        pipeline.generate_parsed_pages = bool(cfg.get("generate_parsed_pages", False))

        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)},
        )
        result = converter.convert(
            file_path,
            raises_on_error=False,
            max_num_pages=max_pages,
            max_file_size=max_file_size_mb * 1024 * 1024,
            page_range=(1, max_pages),
        )
        status = getattr(result, "status", None)
        errors = getattr(result, "errors", []) or []
        status_value = getattr(status, "value", str(status or "")).lower()
        if status in {ConversionStatus.FAILURE, ConversionStatus.SKIPPED}:
            message = ";".join(str(err) for err in errors) or "conversion_failed"
            raise RuntimeError(f"docling_conversion_failed:{status_value}:{message}")

        document_obj = getattr(result, "document", result)
        if document_obj is None:
            message = ";".join(str(err) for err in errors) or "empty_document"
            raise RuntimeError(f"docling_conversion_failed:{status_value}:{message}")

        if hasattr(document_obj, "export_to_dict"):
            payload = document_obj.export_to_dict()
        elif hasattr(document_obj, "to_dict"):
            payload = document_obj.to_dict()
        elif isinstance(document_obj, dict):
            payload = document_obj
        else:
            raise RuntimeError("docling output does not expose a dictionary payload")

        if not isinstance(payload, dict):
            raise RuntimeError("docling payload is not a dictionary")
        payload["_provider_meta"] = {
            "provider": self.name,
            "status": status_value or "unknown",
            "do_ocr": do_ocr,
            "max_pages": max_pages,
        }
        return payload


@dataclass(slots=True)
class MinerULayoutProvider:
    """MinerU-backed extraction provider."""

    name: str = "mineru"

    def extract(self, file_path: str) -> dict[str, Any]:
        try:
            mineru_mod = importlib.import_module("mineru")
        except ImportError as exc:
            raise RuntimeError("mineru provider is not installed") from exc

        parser = None
        for ctor_name in ("MinerU", "MinerUParser", "DocumentParser"):
            ctor = getattr(mineru_mod, ctor_name, None)
            if callable(ctor):
                parser = ctor()
                break
        if parser is None:
            raise RuntimeError("mineru provider parser class not found")

        for method_name in ("parse", "extract", "process"):
            method = getattr(parser, method_name, None)
            if callable(method):
                payload = method(file_path)
                break
        else:
            raise RuntimeError("mineru provider has no parse/extract/process method")

        if hasattr(payload, "to_dict"):
            payload = payload.to_dict()
        if not isinstance(payload, dict):
            raise RuntimeError("mineru payload is not a dictionary")
        return cast(dict[str, Any], payload)


class LayoutAwareExtractor(BaseExtractionStrategy):
    """Provider-normalized layout extraction for complex docs."""

    name = "layout_aware"

    def __init__(self, provider: LayoutProvider | None = None) -> None:
        self.provider = provider

    def estimate_cost(self, rules: dict, page_count: int) -> float:
        costing = rules.get("extraction", {}).get("costing", {})
        base = float(costing.get("layout_base", 0.01))
        per_page = float(costing.get("layout_per_page", 0.001))
        return base + (per_page * max(1, page_count))

    def _provider_from_rules(
        self, rules: dict[str, Any], profile: DocumentProfile | None = None
    ) -> LayoutProvider:
        configured = str(rules.get("extraction", {}).get("layout_aware", {}).get("provider", "docling")).strip().lower()
        if configured == "docling":
            return DoclingLayoutProvider(
                provider_rules=cast(
                    dict[str, Any], rules.get("extraction", {}).get("layout_aware", {})
                ),
                document_profile=profile,
            )
        if configured == "mineru":
            return MinerULayoutProvider()
        raise RuntimeError(f"unsupported_layout_provider:{configured}")

    @staticmethod
    def _classify_provider_error(exc: Exception) -> str:
        text = str(exc).lower()
        if "not installed" in text:
            return "layout_provider_not_available"
        if "timeout" in text or "timed out" in text:
            return "layout_provider_timeout"
        if "conversion_failed" in text:
            return "layout_provider_conversion_failed"
        return "layout_provider_error"

    @staticmethod
    def _as_bbox(raw: dict[str, Any] | None, fallback: tuple[float, float, float, float]) -> BoundingBox:
        raw = raw or {}
        # Support generic x0/y0/x1/y1 and Docling l/t/r/b formats.
        x0 = raw.get("x0", raw.get("l", fallback[0]))
        y0 = raw.get("y0", raw.get("t", fallback[1]))
        x1 = raw.get("x1", raw.get("r", fallback[2]))
        y1 = raw.get("y1", raw.get("b", fallback[3]))
        return BoundingBox(
            x0=float(x0 or fallback[0]),
            y0=float(y0 or fallback[1]),
            x1=float(x1 or fallback[2]),
            y1=float(y1 or fallback[3]),
        )

    def _normalize_payload(self, doc_id: str, payload: dict[str, Any]) -> tuple[list[TextBlock], list[StructuredTable], list[FigureBlock], int]:
        page_count = int(
            payload.get("page_count")
            or payload.get("metadata", {}).get("page_count")
            or (len(payload.get("pages") or {}) if isinstance(payload.get("pages"), dict) else 0)
            or 1
        )
        text_blocks: list[TextBlock] = []
        tables: list[StructuredTable] = []
        figures: list[FigureBlock] = []

        raw_blocks = payload.get("text_blocks") or payload.get("blocks") or payload.get("texts") or []
        for idx, block in enumerate(raw_blocks):
            if not isinstance(block, dict):
                continue
            text = str(block.get("text", block.get("orig", ""))).strip()
            if not text:
                continue
            # Docling encodes provenance under `prov` list.
            prov_list = block.get("prov") if isinstance(block.get("prov"), list) else []
            first_prov = prov_list[0] if prov_list and isinstance(prov_list[0], dict) else {}
            page_number = max(1, int(block.get("page_number", first_prov.get("page_no", 1)) or 1))
            bbox = self._as_bbox(
                block.get("bounding_box") or first_prov.get("bbox"),
                (0.0, 0.0, 1.0, 1.0),
            )
            text_blocks.append(
                TextBlock(
                    id=str(block.get("id") or f"ltb-{page_number}-{idx}"),
                    page_number=page_number,
                    bounding_box=bbox,
                    reading_order=max(0, int(block.get("reading_order", idx) or idx)),
                    block_type=str(block.get("block_type", "paragraph") or "paragraph"),
                    text=text,
                    content_hash=str(block.get("content_hash") or stable_content_hash(text)),
                    confidence=float(block.get("confidence", 0.9) or 0.9),
                )
            )

        raw_tables = payload.get("tables") or []
        for idx, table in enumerate(raw_tables):
            if not isinstance(table, dict):
                continue
            prov_list = table.get("prov") if isinstance(table.get("prov"), list) else []
            first_prov = prov_list[0] if prov_list and isinstance(prov_list[0], dict) else {}
            page_number = max(1, int(table.get("page_number", first_prov.get("page_no", 1)) or 1))

            headers = [str(v) for v in (table.get("headers") or [])]
            rows = [[str(c) for c in row] for row in (table.get("rows") or []) if isinstance(row, list)]

            # Docling table format: data.table_cells with row/col indices.
            if (not headers and not rows) and isinstance(table.get("data"), dict):
                table_data = table.get("data") or {}
                table_cells = table_data.get("table_cells") or []
                if isinstance(table_cells, list) and table_cells:
                    max_row = 0
                    for cell in table_cells:
                        if isinstance(cell, dict):
                            max_row = max(max_row, int(cell.get("start_row_offset_idx", 0) or 0))
                    reconstructed: list[list[str]] = [[] for _ in range(max_row + 1)]
                    for cell in table_cells:
                        if not isinstance(cell, dict):
                            continue
                        row_idx = int(cell.get("start_row_offset_idx", 0) or 0)
                        col_idx = int(cell.get("start_col_offset_idx", 0) or 0)
                        while len(reconstructed[row_idx]) <= col_idx:
                            reconstructed[row_idx].append("")
                        reconstructed[row_idx][col_idx] = str(cell.get("text", "") or "")
                    if reconstructed:
                        headers = reconstructed[0]
                        rows = reconstructed[1:] if len(reconstructed) > 1 else []

            if not headers and not rows:
                continue
            serial = "|".join(headers) + "\n" + "\n".join("|".join(r) for r in rows)
            tables.append(
                StructuredTable(
                    id=str(table.get("id") or f"tbl-{page_number}-{idx}"),
                    page_number=page_number,
                    bounding_box=self._as_bbox(
                        table.get("bounding_box") or first_prov.get("bbox"),
                        (0.0, 0.0, 1.0, 1.0),
                    ),
                    caption=table.get("caption"),
                    headers=headers,
                    rows=rows,
                    content_hash=str(table.get("content_hash") or stable_content_hash(serial)),
                    confidence=float(table.get("confidence", 0.85) or 0.85),
                )
            )

        raw_figures = payload.get("figures") or payload.get("pictures") or []
        for idx, figure in enumerate(raw_figures):
            if not isinstance(figure, dict):
                continue
            prov_list = figure.get("prov") if isinstance(figure.get("prov"), list) else []
            first_prov = prov_list[0] if prov_list and isinstance(prov_list[0], dict) else {}
            page_number = max(1, int(figure.get("page_number", first_prov.get("page_no", 1)) or 1))
            caption = str(figure.get("caption", "") or "")
            serial = f"{caption}-{page_number}-{idx}"
            figures.append(
                FigureBlock(
                    id=str(figure.get("id") or f"fig-{page_number}-{idx}"),
                    page_number=page_number,
                    bounding_box=self._as_bbox(
                        figure.get("bounding_box") or first_prov.get("bbox"),
                        (0.0, 0.0, 1.0, 1.0),
                    ),
                    caption=caption or None,
                    figure_type=str(figure.get("figure_type", "image") or "image"),
                    content_hash=str(figure.get("content_hash") or stable_content_hash(serial)),
                    confidence=float(figure.get("confidence", 0.8) or 0.8),
                )
            )

        return text_blocks, tables, figures, max(1, page_count)

    def extract(self, context: ExtractionContext) -> StrategyResult:
        if not Path(context.file_path).exists():
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=0.0,
                document=None,
                cost_estimate=0.0,
                error="file_not_found",
            )

        provider = self.provider or self._provider_from_rules(
            context.rules, context.document_profile
        )
        try:
            provider_payload = provider.extract(context.file_path)
        except Exception as exc:
            code = self._classify_provider_error(exc)
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=0.0,
                document=None,
                cost_estimate=self.estimate_cost(context.rules, 1),
                metadata={"provider": getattr(provider, "name", "unknown")},
                error=f"{code}:{exc}",
            )

        text_blocks, tables, figures, page_count = self._normalize_payload(context.doc_id, provider_payload)
        provider_meta = cast(dict[str, Any], provider_payload.get("_provider_meta", {}))

        richness = min(1.0, (len(text_blocks) / 80.0) + (len(tables) * 0.15) + (len(figures) * 0.10))
        confidence = max(0.0, min(1.0, 0.45 + richness))

        if (
            not text_blocks
            and not tables
            and not figures
            and isinstance(provider, DoclingLayoutProvider)
            and not bool(provider_meta.get("do_ocr", False))
        ):
            try:
                retry_payload = provider.extract(context.file_path, force_ocr=True)
                text_blocks, tables, figures, page_count = self._normalize_payload(
                    context.doc_id, retry_payload
                )
                provider_meta = cast(dict[str, Any], retry_payload.get("_provider_meta", provider_meta))
                richness = min(
                    1.0,
                    (len(text_blocks) / 80.0)
                    + (len(tables) * 0.15)
                    + (len(figures) * 0.10),
                )
                confidence = max(0.0, min(1.0, 0.45 + richness))
            except Exception:
                pass

        if not text_blocks and not tables and not figures:
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=confidence,
                document=None,
                cost_estimate=self.estimate_cost(context.rules, page_count),
                metadata={
                    "provider": getattr(provider, "name", "unknown"),
                    "provider_status": provider_meta.get("status", "unknown"),
                },
                error="no_layout_content",
            )

        document = ExtractedDocument(
            doc_id=context.doc_id,
            strategy_used=self.name,
            confidence_score=confidence,
            metadata={
                "page_count": page_count,
                "provider": getattr(provider, "name", "unknown"),
                "provider_status": provider_meta.get("status", "unknown"),
                "provider_ocr_enabled": bool(provider_meta.get("do_ocr", False)),
                "reading_order_reconstructed": True,
            },
            text_blocks=text_blocks,
            tables=tables,
            figures=figures,
        )

        return StrategyResult(
            strategy_used=self.name,
            confidence_score=confidence,
            document=document,
            cost_estimate=self.estimate_cost(context.rules, page_count),
            metadata={
                "page_count": page_count,
                "provider": getattr(provider, "name", "unknown"),
                "provider_status": provider_meta.get("status", "unknown"),
                "provider_ocr_enabled": bool(provider_meta.get("do_ocr", False)),
            },
        )
