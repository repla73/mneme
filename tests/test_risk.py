from mneme.risk import ContextRiskSentinel, ContextSignals, RiskLevel


def test_authoritative_high_usage_is_red():
    report = ContextRiskSentinel().assess(
        ContextSignals(
            used_tokens=180_000,
            context_window=200_000,
            token_metrics_authoritative=True,
        )
    )
    assert report.level == RiskLevel.RED
    assert report.authoritative_usage_ratio == 0.9


def test_untrusted_token_numbers_are_not_used_as_meter():
    report = ContextRiskSentinel().assess(
        ContextSignals(used_tokens=999_999, context_window=100_000, token_metrics_authoritative=False)
    )
    assert report.level == RiskLevel.GREEN
    assert report.authoritative_usage_ratio is None
    assert any("non-authoritative" in reason for reason in report.reasons)


def test_behavioral_failures_raise_risk():
    report = ContextRiskSentinel().assess(
        ContextSignals(forgotten_constraints=2, user_memory_corrections=2)
    )
    assert report.level == RiskLevel.RED
