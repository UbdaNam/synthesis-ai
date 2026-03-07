from src.chunking.hash_generator import generate_ldu_hash


def test_hash_generator_is_stable():
    value_1 = generate_ldu_hash(
        content="hello world",
        chunk_type="section_text",
        page_refs=[1],
        parent_section="Overview",
        metadata={"a": 1},
    )
    value_2 = generate_ldu_hash(
        content="hello   world",
        chunk_type="section_text",
        page_refs=[1],
        parent_section="Overview",
        metadata={"a": 1},
    )
    assert value_1 == value_2
