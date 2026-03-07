"""Stage 2 extraction router with deterministic escalation + ledger logging."""

from __future__ import annotations

import json
import time
from pathlib import Path
from collections.abc import Callable
from typing import Any

import yaml

from src.models.document_profile import DocumentProfile
from src.models.extracted_document import ExtractionAttemptRecord, ExtractionLedgerEntry, StrategyName
from src.models.graph_state import GraphState
from src.strategies.base import BaseExtractionStrategy, ExtractionContext, StrategyResult
from src.strategies.fast_text import FastTextExtractor
from src.strategies.layout_aware import LayoutAwareExtractor
from src.strategies.vision import VisionExtractor


def _load_rules(config_path: str) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as stream:
        loaded = yaml.safe_load(stream) or {}
    if "extraction" not in loaded:
        loaded["extraction"] = {}
    return loaded


class ExtractionRouter:
    """Deterministic strategy router with confidence-gated escalation."""

    ORDER: tuple[StrategyName, ...] = ("fast_text", "layout_aware", "vision")

    def __init__(
        self,
        config_path: str = "rubric/extraction_rules.yaml",
        ledger_path: str = ".refinery/extraction_ledger.jsonl",
        strategy_registry: dict[StrategyName, BaseExtractionStrategy] | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self.config_path = config_path
        self.rules = _load_rules(config_path)
        self.ledger_path = Path(ledger_path)
        self.timer = timer or time.perf_counter
        self.strategy_registry = strategy_registry or {
            "fast_text": FastTextExtractor(),
            "layout_aware": LayoutAwareExtractor(),
            "vision": VisionExtractor(),
        }

    def _threshold(self, strategy: StrategyName) -> float:
        thresholds = self.rules.get("extraction", {}).get("escalation", {}).get("acceptance_thresholds", {})
        return float(thresholds.get(strategy, 0.75))

    def _rule_reference(self) -> str:
        return str(self.rules.get("extraction", {}).get("router", {}).get("rule_version", "extraction-v1"))

    def _budget_cap(self) -> float:
        return float(self.rules.get("extraction", {}).get("vision", {}).get("budget_cap_default", 0.15))

    def _append_ledger(self, entry: ExtractionLedgerEntry) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry.model_dump(mode="json"), sort_keys=True))
            stream.write("\n")

    def select_initial_strategy(self, profile: DocumentProfile) -> StrategyName:
        if profile.origin_type == "scanned_image":
            return "vision"
        if profile.layout_complexity in {"multi_column", "table_heavy", "mixed"}:
            return "layout_aware"
        if profile.origin_type in {"mixed", "form_fillable"}:
            return "layout_aware"
        return "fast_text"

    def _handwriting_detected(self, state: GraphState) -> bool:
        marker = str(state.file_path).lower()
        if "handwriting" in marker or "handwritten" in marker:
            return True
        hints = self.rules.get("extraction", {}).get("vision", {}).get("handwriting_doc_ids", [])
        return state.doc_id in set(hints)

    def _next_strategy(self, current: StrategyName) -> StrategyName | None:
        try:
            idx = self.ORDER.index(current)
        except ValueError:
            return None
        if idx + 1 >= len(self.ORDER):
            return None
        return self.ORDER[idx + 1]

    def _budget_would_overflow(self, budget_spent: float, estimated_next_cost: float) -> bool:
        return (budget_spent + max(0.0, estimated_next_cost)) > self._budget_cap()

    def _resolve_start_strategy(self, state: GraphState) -> StrategyName:
        if state.document_profile is None:
            raise ValueError("DocumentProfile missing from state")

        forced_vision = self._handwriting_detected(state)
        initial = self.select_initial_strategy(state.document_profile)
        if forced_vision:
            return "vision"
        return initial

    def extract_node(self, state: GraphState) -> GraphState:
        if state.document_profile is None:
            return state.model_copy(
                update={
                    "extracted_document": None,
                    "extraction_error": "missing_document_profile",
                }
            )

        attempts: list[ExtractionAttemptRecord] = []
        budget_spent = 0.0
        current_strategy = self._resolve_start_strategy(state)

        while current_strategy is not None:
            strategy = self.strategy_registry[current_strategy]

            # Budget pre-check for vision calls.
            if current_strategy == "vision" and hasattr(strategy, "estimate_tokens") and hasattr(strategy, "estimate_cost"):
                try:
                    est_tokens = int(strategy.estimate_tokens(page_count=1, rules=self.rules))
                    est_cost = float(strategy.estimate_cost(est_tokens, self.rules))
                except Exception:
                    est_tokens = 0
                    est_cost = 0.0
                if self._budget_would_overflow(budget_spent, est_cost):
                    rec = ExtractionAttemptRecord(
                        doc_id=state.doc_id,
                        attempt_index=len(attempts) + 1,
                        strategy_used="vision",
                        confidence_score=0.0,
                        cost_estimate=0.0,
                        usage_tokens=0,
                        processing_time=0.0,
                        escalated=bool(attempts),
                        rule_reference=self._rule_reference(),
                        final_disposition="failed_closed",
                        error_reason="budget_cap_exceeded",
                    )
                    attempts.append(rec)
                    self._append_ledger(
                        ExtractionLedgerEntry(
                            doc_id=state.doc_id,
                            strategy_used="vision",
                            confidence_score=0.0,
                            cost_estimate=0.0,
                            processing_time=0.0,
                            escalation_flag=True,
                            threshold_rule_reference=self._rule_reference(),
                            usage_tokens=0,
                            budget_cap=self._budget_cap(),
                            budget_spent=budget_spent,
                            final_disposition="failed_closed",
                        )
                    )
                    return state.model_copy(
                        update={
                            "extracted_document": None,
                            "extraction_attempts": attempts,
                            "extraction_error": "budget_cap_exceeded",
                        }
                    )

            context = ExtractionContext(
                doc_id=state.doc_id,
                file_path=state.file_path,
                document_profile=state.document_profile,
                rules=self.rules,
                attempt_index=len(attempts) + 1,
                budget_spent=budget_spent,
            )

            started = self.timer()
            try:
                result: StrategyResult = strategy.extract(context)
                elapsed = max(0.0, self.timer() - started)
            except Exception as exc:
                result = StrategyResult(
                    strategy_used=current_strategy,
                    confidence_score=0.0,
                    document=None,
                    cost_estimate=0.0,
                    usage_tokens=0,
                    error=f"strategy_error:{exc.__class__.__name__}",
                )
                elapsed = max(0.0, self.timer() - started)

            budget_spent += max(0.0, result.cost_estimate)
            threshold = self._threshold(current_strategy)
            accepted = result.document is not None and result.confidence_score >= threshold
            disposition = "accepted" if accepted else "escalated"
            next_strategy = self._next_strategy(current_strategy)
            if not accepted and next_strategy is None:
                disposition = "failed_closed"

            record = ExtractionAttemptRecord(
                doc_id=state.doc_id,
                attempt_index=len(attempts) + 1,
                strategy_used=current_strategy,
                confidence_score=result.confidence_score,
                cost_estimate=max(0.0, result.cost_estimate),
                usage_tokens=max(0, result.usage_tokens),
                processing_time=elapsed,
                escalated=bool(attempts),
                rule_reference=self._rule_reference(),
                final_disposition=disposition,
                error_reason=result.error,
            )
            attempts.append(record)

            self._append_ledger(
                ExtractionLedgerEntry(
                    doc_id=state.doc_id,
                    strategy_used=current_strategy,
                    confidence_score=result.confidence_score,
                    cost_estimate=max(0.0, result.cost_estimate),
                    processing_time=elapsed,
                    escalation_flag=bool(attempts[:-1]),
                    threshold_rule_reference=self._rule_reference(),
                    usage_tokens=max(0, result.usage_tokens),
                    budget_cap=self._budget_cap(),
                    budget_spent=budget_spent,
                    final_disposition=disposition,
                )
            )

            if accepted:
                return state.model_copy(
                    update={
                        "extracted_document": result.document,
                        "extraction_attempts": attempts,
                        "extraction_error": None,
                    }
                )

            current_strategy = next_strategy

        return state.model_copy(
            update={
                "extracted_document": None,
                "extraction_attempts": attempts,
                "extraction_error": "all_strategies_below_threshold",
            }
        )
