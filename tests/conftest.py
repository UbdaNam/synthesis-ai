"""Shared test fixtures for Stage 1 triage tests."""

from __future__ import annotations

import sys
from pathlib import Path

import shutil
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def workspace_tmp() -> Path:
    base = ROOT / ".test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    target = base / str(uuid.uuid4())
    target.mkdir(parents=True, exist_ok=True)
    yield target
    shutil.rmtree(target, ignore_errors=True)


@pytest.fixture()
def temp_config(workspace_tmp: Path) -> Path:
    config = workspace_tmp / "extraction_rules.yaml"
    config.write_text(
        "\n".join(
            [
                "triage:",
                "  deterministic_version: triage-v1",
                "  origin_thresholds:",
                "    native_char_density_min: 0.002",
                "    native_image_ratio_max: 0.20",
                "    scanned_char_count_max: 20",
                "    scanned_image_ratio_min: 0.60",
                "  layout_thresholds:",
                "    multi_column_x_clusters_min: 2",
                "    table_grid_score_min: 0.35",
                "    figure_heavy_image_ratio_min: 0.45",
                "  language:",
                "    fallback_code: und",
                "    fallback_confidence: 0.5",
                "  domain_keywords:",
                "    financial: [balance, invoice, revenue, tax]",
                "    legal: [agreement, clause, contract, statute]",
                "    technical: [architecture, api, module, protocol]",
                "    medical: [diagnosis, patient, treatment, clinical]",
                "  cost_mapping:",
                "    scanned_image: needs_vision_model",
                "    figure_heavy: needs_vision_model",
                "    layout_complex: needs_layout_model",
                "    default: fast_text_sufficient",
                "extraction:",
                "  router:",
                "    rule_version: extraction-v1-test",
                "  fast_text:",
                "    confidence_signals:",
                "      char_count_min: 50",
                "      char_density_min: 0.0008",
                "      image_ratio_max: 0.40",
                "      font_metadata_required: false",
                "    weights:",
                "      char_count: 0.35",
                "      char_density: 0.35",
                "      image_to_page_ratio: 0.20",
                "      font_metadata_presence: 0.10",
                "  escalation:",
                "    acceptance_thresholds:",
                "      fast_text: 0.70",
                "      layout_aware: 0.75",
                "      vision: 0.78",
                "  layout_aware:",
                "    provider: docling",
                "    providers:",
                "      docling:",
                "        enabled: true",
                "      mineru:",
                "        enabled: false",
                "  vision:",
                "    provider: openrouter",
                "    model: openrouter/auto",
                "    prompt_template_version: v1-test",
                "    structured_output_method: json_schema",
                "    structured_output_retry_max: 1",
                "    budget_cap_default: 0.15",
                "    tokens_per_page_estimate: 1200",
                "    base_prompt_tokens: 300",
                "    cost_per_1k_tokens: 0.006",
                "    handwriting_doc_ids: []",
                "  costing:",
                "    fast_text_base: 0.001",
                "    fast_text_per_page: 0.0002",
                "    layout_base: 0.01",
                "    layout_per_page: 0.001",
            ]
        ),
        encoding="utf-8",
    )
    return config


@pytest.fixture()
def stage2_sample_pdf() -> Path:
    return ROOT / "sample_files/background-checks.pdf"
