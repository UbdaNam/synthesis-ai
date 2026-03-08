import pytest
from pydantic import ValidationError

from src.models.chunk_relationship import ChunkRelationship


def test_chunk_relationship_supports_required_types():
    relationship = ChunkRelationship(
        id="rel-1",
        doc_id="doc-1",
        source_chunk_id="ldu-1",
        target_chunk_id="ldu-2",
        relationship_type="references_table",
        target_label="Table 1",
        resolved=True,
    )
    assert relationship.relationship_type == "references_table"


def test_unresolved_chunk_relationship_requires_target_label():
    with pytest.raises(ValidationError):
        ChunkRelationship(
            id="rel-1",
            doc_id="doc-1",
            source_chunk_id="ldu-1",
            relationship_type="references_section",
            resolved=False,
        )
