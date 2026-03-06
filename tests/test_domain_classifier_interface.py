from src.agents.triage import DomainClassifierStrategy, KeywordDomainClassifier


def test_keyword_classifier_conforms_interface():
    classifier = KeywordDomainClassifier({"financial": ["invoice"]})
    assert isinstance(classifier, DomainClassifierStrategy)
    assert classifier.classify("invoice amount due") in {
        "financial",
        "legal",
        "technical",
        "medical",
        "general",
    }

