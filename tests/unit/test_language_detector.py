from synthesis_ai.triage.language_detector import LanguageDetector


def test_language_detection_english_sample() -> None:
    result = LanguageDetector().detect("This is an English sentence for language detection.")
    assert result.code
    assert 0.0 <= result.confidence <= 1.0


def test_language_detection_non_english_sample() -> None:
    result = LanguageDetector().detect("Bonjour, ceci est un document rédigé en français.")
    assert result.code
    assert 0.0 <= result.confidence <= 1.0


def test_language_detection_is_deterministic() -> None:
    detector = LanguageDetector()
    text = "This sentence should always get the same language output."
    first = detector.detect(text)
    second = detector.detect(text)
    assert first == second

