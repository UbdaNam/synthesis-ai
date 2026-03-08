import sqlite3

from src.query.fact_table_extractor import FactTableExtractor
from tests.unit._stage5_test_utils import build_stage5_state


def test_fact_table_extractor_creates_schema_and_persists_rows(workspace_tmp):
    state, rules = build_stage5_state(workspace_tmp)
    extractor = FactTableExtractor(rules)
    info = extractor.extract_and_store(state.doc_id, state.chunked_document, document_name=state.doc_id)
    assert info["fact_count"] >= 1
    with sqlite3.connect(info["facts_db_path"]) as connection:
        count = connection.execute("SELECT COUNT(*) FROM facts WHERE doc_id = ?", (state.doc_id,)).fetchone()[0]
    assert count >= 1
