"""Real SQLite-backed structured fact query tool."""

from __future__ import annotations

import sqlite3
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from src.models.extracted_document import BoundingBox
from src.models.query_result import StructuredQueryResult, StructuredQueryRow
from src.query import QueryArtifactPaths, QueryStageError, load_rules
from src.query.fact_table_extractor import FactTableExtractor


class StructuredQueryToolInput(BaseModel):
    """Arguments accepted by the structured_query tool."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    fact_filters: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)


class StructuredQueryService:
    """Execute deterministic SQL queries against the Stage 5 FactTable."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or load_rules()
        self.paths = QueryArtifactPaths(self.rules)
        self.extractor = FactTableExtractor(self.rules)
        self.extractor.ensure_schema()

    def query(self, doc_id: str, query: str, fact_filters: list[str] | None = None, limit: int = 5) -> StructuredQueryResult:
        fact_filters = fact_filters or []
        sql, params = self._build_sql(doc_id, query, fact_filters, limit)
        try:
            with sqlite3.connect(self.paths.facts_db_path) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute(sql, params).fetchall()
        except sqlite3.Error as exc:  # pragma: no cover
            raise QueryStageError("structured_query_failed") from exc
        normalized = [self._normalize_row(row) for row in rows]
        return StructuredQueryResult(doc_id=doc_id, query=query, sql=sql, rows=normalized)

    def build_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=lambda doc_id, query, fact_filters=None, limit=5: self.query(doc_id=doc_id, query=query, fact_filters=fact_filters or [], limit=limit).model_dump(mode="json"),
            name="structured_query",
            description="Query the local SQLite FactTable for precise numerical and key-value facts with source provenance.",
            args_schema=StructuredQueryToolInput,
        )

    def _build_sql(self, doc_id: str, query: str, fact_filters: list[str], limit: int) -> tuple[str, list[Any]]:
        lowered = query.lower()
        terms = [term.lower() for term in fact_filters if term.strip()]
        if not terms:
            stopwords = {
                "a",
                "about",
                "an",
                "and",
                "are",
                "does",
                "for",
                "from",
                "how",
                "in",
                "is",
                "of",
                "show",
                "tell",
                "that",
                "the",
                "this",
                "to",
                "was",
                "what",
                "which",
                "with",
            }
            candidate_terms = [
                token
                for token in lowered.replace("?", " ").replace(",", " ").split()
                if len(token) > 2 and token not in stopwords
            ]
            terms = candidate_terms[:4]
        normalized_terms = [term.strip().lower() for term in terms if term.strip()]
        if not normalized_terms:
            normalized_terms = [lowered.strip()]
        score_terms = normalized_terms[:4]
        score_clauses: list[str] = []
        params: list[Any] = []
        for term in score_terms:
            score_clauses.append("CASE WHEN normalized_name = ? THEN 4 ELSE 0 END")
            params.append(term)
            score_clauses.append("CASE WHEN normalized_name LIKE ? THEN 2 ELSE 0 END")
            params.append(f"%{term}%")
            score_clauses.append("CASE WHEN fact_name LIKE ? THEN 1 ELSE 0 END")
            params.append(f"%{term}%")
            score_clauses.append("CASE WHEN fact_value LIKE ? THEN 1 ELSE 0 END")
            params.append(f"%{term}%")
        sql = (
            "SELECT fact_id, doc_id, fact_name, fact_value, value_type, unit, period, "
            "source_chunk_id, document_name, page_number, bounding_box_json, content_hash, section_id, "
            + " + ".join(score_clauses)
            + " AS score FROM facts WHERE doc_id = ?"
        )
        params.append(doc_id)
        like_clauses: list[str] = []
        for term in normalized_terms:
            like_clauses.extend(
                [
                    "normalized_name = ?",
                    "normalized_name LIKE ?",
                    "fact_name LIKE ?",
                    "fact_value LIKE ?",
                ]
            )
            params.extend([term, f"%{term}%", f"%{term}%", f"%{term}%"])
        sql += " AND (" + " OR ".join(like_clauses) + ") ORDER BY score DESC, page_number ASC LIMIT ?"
        params.append(limit)
        return sql, params

    @staticmethod
    def _normalize_row(row: sqlite3.Row) -> StructuredQueryRow:
        bbox = BoundingBox.model_validate_json(row["bounding_box_json"])
        return StructuredQueryRow(
            fact_id=row["fact_id"],
            doc_id=row["doc_id"],
            fact_name=row["fact_name"],
            fact_value=row["fact_value"],
            value_type=row["value_type"],
            unit=row["unit"],
            period=row["period"],
            source_chunk_id=row["source_chunk_id"],
            document_name=row["document_name"],
            page_number=row["page_number"],
            bounding_box=bbox,
            content_hash=row["content_hash"],
            section_id=row["section_id"],
            score=float(row["score"] or 0.0),
        )
