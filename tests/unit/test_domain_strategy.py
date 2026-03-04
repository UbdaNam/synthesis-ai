from synthesis_ai.models.document_profile import DomainHint
from synthesis_ai.triage.domain.keyword_strategy import KeywordDomainClassifier


def test_domain_strategy_returns_allowed_value() -> None:
    value = KeywordDomainClassifier().classify("architecture module api protocol")
    assert value in {
        DomainHint.FINANCIAL,
        DomainHint.LEGAL,
        DomainHint.TECHNICAL,
        DomainHint.MEDICAL,
        DomainHint.GENERAL,
    }

