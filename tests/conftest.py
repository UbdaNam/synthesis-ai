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
            ]
        ),
        encoding="utf-8",
    )
    return config
