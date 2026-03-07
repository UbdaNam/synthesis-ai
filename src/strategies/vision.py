"""Strategy C: multimodal vision extraction via OpenRouter + LangChain."""

from __future__ import annotations

import base64
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import pdfplumber
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.config.env import ensure_env_loaded
from src.models.extracted_document import BoundingBox, ExtractedDocument, TextBlock, stable_content_hash
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult


class VisionClient(Protocol):
    """Client contract for structured multimodal extraction."""

    def invoke_structured(self, prompt: str, image_data_uris: list[str], config: dict[str, Any]) -> dict[str, Any]:
        """Return structured extraction payload."""


class _VisionRawTextBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box: dict[str, float] | None = None


class _VisionStructuredResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text_blocks: list[_VisionRawTextBlock] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    figures: list[dict[str, Any]] = Field(default_factory=list)
    handwriting_detected: bool = False
    usage_tokens: int = Field(default=0, ge=0)


@dataclass(slots=True)
class OpenRouterVisionClient:
    """Real OpenRouter-backed multimodal client (LangChain ChatOpenRouter)."""

    model_name: str = "openrouter/auto"

    def _build_model(self, config: dict[str, Any]):
        ensure_env_loaded()
        try:
            from langchain_openrouter import ChatOpenRouter
        except ImportError as exc:
            raise RuntimeError("langchain-openrouter is required for VisionExtractor") from exc

        rules = config.get("extraction", {}).get("vision", {})
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

        model_name = str(rules.get("model", self.model_name))
        temperature = float(rules.get("temperature", 0.0))
        max_retries = int(rules.get("max_retries", 2))

        return ChatOpenRouter(
            model=model_name,
            temperature=temperature,
            max_retries=max_retries,
        )

    @staticmethod
    def _extract_token_usage(raw_message: Any) -> int:
        usage_total = 0
        response_metadata = getattr(raw_message, "response_metadata", {}) or {}
        usage_meta = getattr(raw_message, "usage_metadata", {}) or {}

        token_usage = response_metadata.get("token_usage", {})
        if isinstance(token_usage, dict):
            usage_total = int(
                token_usage.get("total_tokens")
                or (token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0))
                or 0
            )
        if usage_total <= 0 and isinstance(usage_meta, dict):
            usage_total = int(usage_meta.get("total_tokens") or 0)
        return max(0, usage_total)

    def invoke_structured(self, prompt: str, image_data_uris: list[str], config: dict[str, Any]) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage

        model = self._build_model(config)
        vision_rules = config.get("extraction", {}).get("vision", {})
        structured_method = str(vision_rules.get("structured_output_method", "json_schema"))
        max_parse_retries = max(0, int(vision_rules.get("structured_output_retry_max", 1)))

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image_uri in image_data_uris:
            content.append({"type": "image_url", "image_url": {"url": image_uri}})

        message = HumanMessage(content=content)

        # Best-practice structured output: attach schema to model call and parse typed output.
        structured_model = model.with_structured_output(
            _VisionStructuredResponse,
            method=structured_method,
            include_raw=True,
        )

        last_error: Exception | None = None
        for _ in range(max_parse_retries + 1):
            try:
                result = structured_model.invoke([message])
                parsed_obj = result.get("parsed")
                raw_obj = result.get("raw")
                parsing_error = result.get("parsing_error")
                if parsing_error:
                    raise RuntimeError(f"Vision structured parsing error: {parsing_error}")
                if parsed_obj is None:
                    raise RuntimeError("Vision structured output parsed payload is empty")

                if isinstance(parsed_obj, _VisionStructuredResponse):
                    normalized = parsed_obj
                else:
                    normalized = _VisionStructuredResponse.model_validate(parsed_obj)

                payload = normalized.model_dump(mode="json")
                if int(payload.get("usage_tokens", 0) or 0) <= 0:
                    payload["usage_tokens"] = self._extract_token_usage(raw_obj)
                return payload
            except (ValidationError, RuntimeError) as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                break

        raise RuntimeError(f"Vision structured invocation failed: {last_error}")


class VisionExtractor(BaseExtractionStrategy):
    """High-cost fallback extraction for scanned/handwritten content."""

    name = "vision"

    def __init__(self, client: VisionClient | None = None) -> None:
        self.client = client or OpenRouterVisionClient()

    def estimate_tokens(self, page_count: int, rules: dict[str, Any]) -> int:
        vision = rules.get("extraction", {}).get("vision", {})
        tokens_per_page = int(vision.get("tokens_per_page_estimate", 1200))
        base_prompt_tokens = int(vision.get("base_prompt_tokens", 300))
        return max(0, base_prompt_tokens + (tokens_per_page * max(1, page_count)))

    def estimate_cost(self, usage_tokens: int, rules: dict[str, Any]) -> float:
        vision = rules.get("extraction", {}).get("vision", {})
        cost_per_1k = float(vision.get("cost_per_1k_tokens", 0.006))
        return round((max(0, usage_tokens) / 1000.0) * cost_per_1k, 8)

    def build_prompt(self, context: ExtractionContext) -> str:
        vision_rules = context.rules.get("extraction", {}).get("vision", {})
        prompt_version = vision_rules.get("prompt_template_version", "v1")
        schema_instructions = (
            "Return STRICT JSON with keys: text_blocks, tables, figures, handwriting_detected, usage_tokens. "
            "Each text block needs: text, page_number, bounding_box{x0,y0,x1,y1}."
        )
        return (
            f"PromptVersion={prompt_version}\n"
            f"doc_id={context.doc_id}\n"
            f"origin_type={context.document_profile.origin_type}; layout={context.document_profile.layout_complexity}\n"
            "Extract normalized document structure from provided page images. "
            "Preserve reading order and include only grounded content.\n"
            f"{schema_instructions}"
        )

    def _page_count(self, file_path: str) -> int:
        with pdfplumber.open(file_path) as pdf:
            return max(1, len(pdf.pages))

    def _pdf_to_image_data_uris(self, file_path: str, max_pages: int, dpi: int) -> list[str]:
        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for vision page rendering") from exc

        image_uris: list[str] = []
        with fitz.open(file_path) as document:
            page_limit = min(len(document), max(1, max_pages))
            zoom = max(dpi / 72.0, 1.0)
            matrix = fitz.Matrix(zoom, zoom)
            for i in range(page_limit):
                page = document.load_page(i)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                png_bytes = pix.tobytes("png")
                b64 = base64.b64encode(png_bytes).decode("ascii")
                image_uris.append(f"data:image/png;base64,{b64}")
        return image_uris

    def _normalize_blocks(self, payload: dict[str, Any]) -> tuple[list[TextBlock], bool]:
        blocks: list[TextBlock] = []
        handwriting = bool(payload.get("handwriting_detected", False))
        for idx, block in enumerate(payload.get("text_blocks", []) or []):
            text = str(block.get("text", "")).strip()
            if not text:
                continue
            bbox = block.get("bounding_box", {}) or {}
            x0 = float(bbox.get("x0", 0.0) or 0.0)
            y0 = float(bbox.get("y0", 0.0) or 0.0)
            x1 = float(bbox.get("x1", 0.0) or 0.0)
            y1 = float(bbox.get("y1", 0.0) or 0.0)
            page_number = int(block.get("page_number", 1) or 1)
            blocks.append(
                TextBlock(
                    id=f"vb-{page_number}-{idx}",
                    page_number=max(1, page_number),
                    bounding_box=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
                    reading_order=idx,
                    block_type="paragraph",
                    text=text,
                    content_hash=stable_content_hash(text),
                    confidence=0.9,
                )
            )
        return blocks, handwriting

    def extract(self, context: ExtractionContext) -> StrategyResult:
        if not Path(context.file_path).exists():
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=0.0,
                document=None,
                cost_estimate=0.0,
                usage_tokens=0,
                error="file_not_found",
            )

        page_count = self._page_count(context.file_path)
        estimated_tokens = self.estimate_tokens(page_count=page_count, rules=context.rules)
        estimated_cost = self.estimate_cost(estimated_tokens, context.rules)
        prompt = self.build_prompt(context)

        vision_rules = context.rules.get("extraction", {}).get("vision", {})
        max_pages = int(vision_rules.get("max_pages_per_request", 4))
        render_dpi = int(vision_rules.get("render_dpi", 144))

        try:
            image_uris = self._pdf_to_image_data_uris(context.file_path, max_pages=max_pages, dpi=render_dpi)
            payload = self.client.invoke_structured(prompt=prompt, image_data_uris=image_uris, config=context.rules)
        except Exception as exc:
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=0.0,
                document=None,
                cost_estimate=estimated_cost,
                usage_tokens=estimated_tokens,
                metadata={"page_count": page_count},
                error=f"vision_provider_error:{exc}",
            )

        usage_tokens = int(payload.get("usage_tokens", estimated_tokens) or estimated_tokens)
        cost_estimate = self.estimate_cost(usage_tokens, context.rules)
        text_blocks, handwriting_detected = self._normalize_blocks(payload)

        if not text_blocks:
            return StrategyResult(
                strategy_used=self.name,
                confidence_score=0.0,
                document=None,
                cost_estimate=max(cost_estimate, estimated_cost),
                usage_tokens=usage_tokens,
                metadata={"handwriting_detected": handwriting_detected, "page_count": page_count},
                error="no_vision_content",
            )

        density_score = min(1.0, len(text_blocks) / max(1.0, math.sqrt(page_count) * 12.0))
        confidence = max(0.0, min(1.0, 0.55 + (0.45 * density_score)))

        document = ExtractedDocument(
            doc_id=context.doc_id,
            strategy_used=self.name,
            confidence_score=confidence,
            metadata={
                "page_count": page_count,
                "provider": "openrouter",
                "model_name": context.rules.get("extraction", {}).get("vision", {}).get("model", "openrouter/auto"),
                "prompt_template_version": context.rules.get("extraction", {}).get("vision", {}).get("prompt_template_version", "v1"),
                "handwriting_detected": handwriting_detected,
                "usage_tokens": usage_tokens,
                "estimated_cost": cost_estimate,
            },
            text_blocks=text_blocks,
            tables=[],
            figures=[],
        )

        return StrategyResult(
            strategy_used=self.name,
            confidence_score=confidence,
            document=document,
            cost_estimate=cost_estimate,
            usage_tokens=usage_tokens,
            metadata={"handwriting_detected": handwriting_detected, "page_count": page_count},
        )
