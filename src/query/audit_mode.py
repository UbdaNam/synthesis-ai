"""Audit-mode claim verification for the Stage 5 query layer."""

from __future__ import annotations

from typing import Any

from src.models.provenance_chain import ProvenanceChainItem
from src.models.query_result import AuditDecisionDraft, AuditResult, QueryRequest, StructuredQueryRow, SemanticSearchHit


class AuditModeError(RuntimeError):
    """Raised when audit mode cannot produce a valid closed-world result."""


class AuditModeEvaluator:
    """Evaluate claims with the same retrieved evidence used by the query agent."""

    def __init__(self, llm_factory: Any) -> None:
        self.llm_factory = llm_factory

    def evaluate(
        self,
        request: QueryRequest,
        retrieval_path_used: list[str],
        semantic_hits: list[SemanticSearchHit],
        structured_rows: list[StructuredQueryRow],
        provenance_by_id: dict[str, ProvenanceChainItem],
    ) -> AuditResult:
        if not semantic_hits and not structured_rows:
            return AuditResult(
                claim=request.user_query,
                support_status="not_found",
                explanation="No supporting evidence was found for this claim in the available document artifacts.",
                provenance_chain=[],
                retrieval_path_used=retrieval_path_used,
                metadata={"reason": "no_evidence"},
            )

        llm = self.llm_factory()
        messages = [
            (
                "system",
                "You verify claims against supplied document evidence. Classify the claim as supported, not_found, or unverifiable. Use only the supplied evidence IDs and never invent citations.",
            ),
            (
                "human",
                self._render_prompt(request.user_query, semantic_hits, structured_rows),
            ),
        ]
        try:
            decision = llm.with_structured_output(AuditDecisionDraft).invoke(messages)
        except Exception:  # pragma: no cover
            return AuditResult(
                claim=request.user_query,
                support_status="unverifiable",
                explanation="The available evidence could not be verified reliably, so the claim remains unverifiable.",
                provenance_chain=[],
                retrieval_path_used=retrieval_path_used,
                metadata={"reason": "audit_llm_failure"},
            )
        if isinstance(decision, dict):
            decision = AuditDecisionDraft.model_validate(decision)
        provenance = [
            provenance_by_id[evidence_id]
            for evidence_id in [*decision.cited_chunk_ids, *decision.cited_fact_ids]
            if evidence_id in provenance_by_id
        ]
        if decision.support_status == "supported" and not provenance:
            return AuditResult(
                claim=request.user_query,
                support_status="unverifiable",
                explanation="The model marked the claim as supported but did not provide valid source evidence, so the claim remains unverifiable.",
                provenance_chain=[],
                retrieval_path_used=retrieval_path_used,
                metadata={"reason": "missing_supported_provenance"},
            )
        return AuditResult(
            claim=request.user_query,
            support_status=decision.support_status,
            explanation=decision.explanation,
            provenance_chain=provenance,
            retrieval_path_used=retrieval_path_used,
            metadata={
                "cited_chunk_ids": decision.cited_chunk_ids,
                "cited_fact_ids": decision.cited_fact_ids,
            },
        )

    @staticmethod
    def _render_prompt(
        claim: str,
        semantic_hits: list[SemanticSearchHit],
        structured_rows: list[StructuredQueryRow],
    ) -> str:
        semantic_block = "\n\n".join(
            f"Chunk {hit.chunk_id} (pages {','.join(str(page) for page in hit.page_refs)}):\n{hit.content}"
            for hit in semantic_hits[:6]
        )
        fact_block = "\n".join(
            f"Fact {row.fact_id}: {row.fact_name} = {row.fact_value}"
            for row in structured_rows[:6]
        )
        return (
            f"Claim: {claim}\n\n"
            f"Semantic Evidence:\n{semantic_block or 'None'}\n\n"
            f"Structured Facts:\n{fact_block or 'None'}\n\n"
            "Return a grounded classification."
        )
