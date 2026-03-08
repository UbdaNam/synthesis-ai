"""Deterministic FactTable extraction and SQLite storage for Stage 5."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.models.ldu import LDU
from src.query import QueryArtifactPaths, QueryStageError, load_rules, persist_ldu_cache


KEY_VALUE_RE = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9 /&()%-]{1,60}):\s*(?P<value>.+)$")
MONEY_RE = re.compile(r"(?:USD|EUR|KES|GBP|\$|€|£)?\s*-?\d[\d,]*(?:\.\d+)?")
PERCENT_RE = re.compile(r"-?\d+(?:\.\d+)?%")
DATE_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2,9}\s+\d{1,2},\s+\d{4})\b")
PIPE_RE = re.compile(r"\s*\|\s*")
FACT_NAME_HINTS = {
    "revenue",
    "expenditure",
    "expense",
    "income",
    "profit",
    "margin",
    "ratio",
    "fiscal period",
    "period",
    "date",
    "amount due",
    "invoice number",
}


class FactRecord(BaseModel):
    """Normalized fact row prior to SQLite persistence."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    fact_name: str = Field(min_length=1)
    fact_value: str = Field(min_length=1)
    value_type: str = Field(min_length=1)
    unit: str | None = None
    period: str | None = None
    source_chunk_id: str = Field(min_length=1)
    document_name: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    bounding_box_json: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    section_id: str | None = None
    normalized_name: str = Field(min_length=1)
    numeric_value: float | None = None


class FactTableExtractor:
    """Extract and persist financial/numerical facts for structured querying."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or load_rules()
        self.paths = QueryArtifactPaths(self.rules)
        self.paths.ensure()

    def ensure_schema(self) -> Path:
        with sqlite3.connect(self.paths.facts_db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    fact_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    fact_name TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    value_type TEXT NOT NULL,
                    unit TEXT,
                    period TEXT,
                    source_chunk_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    bounding_box_json TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    section_id TEXT,
                    normalized_name TEXT NOT NULL,
                    numeric_value REAL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_facts_doc_name ON facts(doc_id, normalized_name)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_facts_doc_page ON facts(doc_id, page_number)"
            )
            connection.commit()
        return self.paths.facts_db_path

    def extract_and_store(self, doc_id: str, chunks: list[LDU], document_name: str | None = None) -> dict[str, Any]:
        self.ensure_schema()
        persist_ldu_cache(doc_id, chunks, self.rules)
        facts = self.extract_facts(doc_id, chunks, document_name=document_name or doc_id)
        with sqlite3.connect(self.paths.facts_db_path) as connection:
            connection.execute("DELETE FROM facts WHERE doc_id = ?", (doc_id,))
            connection.executemany(
                """
                INSERT INTO facts (
                    fact_id, doc_id, fact_name, fact_value, value_type, unit, period,
                    source_chunk_id, document_name, page_number, bounding_box_json,
                    content_hash, section_id, normalized_name, numeric_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        fact.fact_id,
                        fact.doc_id,
                        fact.fact_name,
                        fact.fact_value,
                        fact.value_type,
                        fact.unit,
                        fact.period,
                        fact.source_chunk_id,
                        fact.document_name,
                        fact.page_number,
                        fact.bounding_box_json,
                        fact.content_hash,
                        fact.section_id,
                        fact.normalized_name,
                        fact.numeric_value,
                    )
                    for fact in facts
                ],
            )
            connection.commit()
        return {
            "doc_id": doc_id,
            "fact_count": len(facts),
            "facts_db_path": str(self.paths.facts_db_path),
            "ldu_cache_path": str(self.paths.ldu_cache_path(doc_id)),
        }

    def extract_facts(self, doc_id: str, chunks: list[LDU], document_name: str) -> list[FactRecord]:
        facts: list[FactRecord] = []
        for chunk in chunks:
            facts.extend(self._extract_key_value_facts(doc_id, chunk, document_name))
            facts.extend(self._extract_table_facts(doc_id, chunk, document_name))
            facts.extend(self._extract_inline_numeric_facts(doc_id, chunk, document_name))
        deduped: dict[str, FactRecord] = {fact.fact_id: fact for fact in facts}
        return list(deduped.values())

    def _extract_key_value_facts(self, doc_id: str, chunk: LDU, document_name: str) -> list[FactRecord]:
        results: list[FactRecord] = []
        for line in chunk.content.splitlines():
            match = KEY_VALUE_RE.match(line.strip())
            if not match:
                continue
            name = match.group("name").strip()
            value = match.group("value").strip()
            if not value:
                continue
            results.append(self._build_fact(doc_id, chunk, document_name, name, value))
        return results

    def _extract_table_facts(self, doc_id: str, chunk: LDU, document_name: str) -> list[FactRecord]:
        if chunk.chunk_type not in {"table", "table_segment"} and "|" not in chunk.content:
            return []
        lines = [line.strip() for line in chunk.content.splitlines() if line.strip()]
        if len(lines) < 2:
            return []
        headers = [part.strip() for part in PIPE_RE.split(lines[0]) if part.strip()]
        if len(headers) < 2:
            return []
        results: list[FactRecord] = []
        for row in lines[1:]:
            cells = [part.strip() for part in PIPE_RE.split(row)]
            if len(cells) != len(headers):
                continue
            row_label = cells[0]
            for header, value in zip(headers[1:], cells[1:], strict=True):
                if not value:
                    continue
                fact_name = f"{row_label} {header}".strip()
                results.append(self._build_fact(doc_id, chunk, document_name, fact_name, value))
        return results

    def _extract_inline_numeric_facts(self, doc_id: str, chunk: LDU, document_name: str) -> list[FactRecord]:
        lowered = chunk.content.lower()
        results: list[FactRecord] = []
        for hint in FACT_NAME_HINTS:
            if hint in lowered:
                value = self._first_value(chunk.content)
                if value:
                    results.append(self._build_fact(doc_id, chunk, document_name, hint.title(), value))
        return results

    def _build_fact(self, doc_id: str, chunk: LDU, document_name: str, name: str, value: str) -> FactRecord:
        normalized_name = self._normalize_name(name)
        value_type, unit, numeric_value = self._infer_value_type(value)
        period = self._extract_period(chunk.content)
        digest = hashlib.sha256(f"{doc_id}:{chunk.id}:{normalized_name}:{value}".encode("utf-8")).hexdigest()[:16]
        return FactRecord(
            fact_id=f"fact-{digest}",
            doc_id=doc_id,
            fact_name=name.strip(),
            fact_value=value.strip(),
            value_type=value_type,
            unit=unit,
            period=period,
            source_chunk_id=chunk.id,
            document_name=document_name,
            page_number=min(chunk.page_refs),
            bounding_box_json=json.dumps(chunk.bounding_box.model_dump(mode="json"), sort_keys=True),
            content_hash=chunk.content_hash,
            section_id=chunk.metadata.get("section_id") or chunk.parent_section,
            normalized_name=normalized_name,
            numeric_value=numeric_value,
        )

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"\s+", " ", name.strip().lower())

    @staticmethod
    def _extract_period(text: str) -> str | None:
        match = DATE_RE.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _first_value(text: str) -> str | None:
        for pattern in (MONEY_RE, PERCENT_RE, DATE_RE):
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def _infer_value_type(value: str) -> tuple[str, str | None, float | None]:
        cleaned = value.replace(",", "").strip()
        if PERCENT_RE.fullmatch(cleaned):
            return "percentage", "%", float(cleaned.rstrip("%"))
        if MONEY_RE.fullmatch(cleaned):
            unit = None
            if cleaned.startswith("USD") or cleaned.startswith("$"):
                unit = "USD"
            elif cleaned.startswith("KES"):
                unit = "KES"
            numeric = re.sub(r"[^0-9.-]", "", cleaned)
            return "currency", unit, float(numeric) if numeric else None
        if DATE_RE.fullmatch(value.strip()):
            return "date", None, None
        numeric = re.sub(r"[^0-9.-]", "", cleaned)
        if numeric and any(ch.isdigit() for ch in numeric):
            return "number", None, float(numeric)
        return "text", None, None


def load_fact_db_path(rules: dict[str, Any] | None = None) -> Path:
    return QueryArtifactPaths(rules).facts_db_path
