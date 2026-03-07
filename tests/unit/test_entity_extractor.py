from src.indexing.entity_extractor import EntityExtractor
from tests.unit._stage4_test_utils import make_ldus


def test_entity_extractor_is_deterministic():
    extractor = EntityExtractor(stopwords=["document"], max_entities=5)
    entities = extractor.extract_for_chunks(make_ldus())
    assert "Acme Corp" in entities
    assert "TABLE-001" in entities
