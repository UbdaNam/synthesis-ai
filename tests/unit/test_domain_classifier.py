from src.models.document_profile import DomainHint
from src.agents.triage.domain.keyword_strategy import KeywordDomainClassifier


def test_keyword_domain_financial() -> None:
    text = "revenue tax balance invoice liability"
    assert KeywordDomainClassifier().classify(text) == DomainHint.FINANCIAL


def test_keyword_domain_general_when_no_match() -> None:
    text = "hello world with no special terms"
    assert KeywordDomainClassifier().classify(text) == DomainHint.GENERAL

