from src.agents.triage import KeywordDomainClassifier


def test_keyword_classifier_financial():
    classifier = KeywordDomainClassifier(
        {
            "financial": ["invoice", "tax"],
            "legal": ["contract"],
            "technical": ["api"],
            "medical": ["patient"],
        }
    )
    assert classifier.classify("Invoice tax summary") == "financial"


def test_keyword_classifier_defaults_to_general():
    classifier = KeywordDomainClassifier({"financial": ["invoice"]})
    assert classifier.classify("no domain terms here") == "general"

