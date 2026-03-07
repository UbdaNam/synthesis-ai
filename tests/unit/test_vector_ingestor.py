from tests.unit._stage4_test_utils import FakeVectorIngestor, make_ldus


def test_vector_ingestor_maps_required_metadata():
    ingestor = FakeVectorIngestor()
    chunks = make_ldus()
    result = ingestor.ingest(
        chunks,
        {chunk.id: {"section_id": "section-1", "section_title": "1 Overview"} for chunk in chunks},
    )
    assert result["ingested_count"] == len(chunks)
