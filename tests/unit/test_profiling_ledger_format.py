import json

from src.models.document_profile import (
    EstimatedExtractionCost,
    LanguageSignal,
    LayoutComplexity,
    OriginType,
)
from src.agents.triage.profiling_ledger_schema import ProfilingLedgerEntry
from src.agents.triage.profiling_logger import ProfilingLogger


def test_profiling_ledger_entry_is_jsonl_and_well_formed(tmp_path) -> None:
    logger = ProfilingLogger(ledger_path=str(tmp_path / "profiling_ledger.jsonl"))
    logger.log(
        ProfilingLedgerEntry(
            doc_id="doc-1",
            char_density=[0.01],
            image_ratio=[0.05],
            layout_signals={"x_cluster_count": 1.0, "grid_alignment_score": 0.2},
            origin_type=OriginType.NATIVE_DIGITAL,
            layout_complexity=LayoutComplexity.SINGLE_COLUMN,
            language=LanguageSignal(code="en", confidence=0.9),
            estimated_extraction_cost=EstimatedExtractionCost.FAST_TEXT_SUFFICIENT,
            processing_time=0.01,
        )
    )
    line = (tmp_path / "profiling_ledger.jsonl").read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["doc_id"] == "doc-1"
    assert "processing_time" in payload

