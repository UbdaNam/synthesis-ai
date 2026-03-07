from src.chunking.token_counter import count_tokens


def test_token_counter_is_deterministic():
    text = "Table 1 shows steady revenue growth."
    assert count_tokens(text) == count_tokens(text)
    assert count_tokens(text) == 7
