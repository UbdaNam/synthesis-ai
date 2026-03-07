from src.models.extracted_document import stable_content_hash


def test_chunking_invariants_hash_is_stable():
    value = "same content"
    assert stable_content_hash(value) == stable_content_hash(value)
