from providers import get_ai_provider


def test_get_ai_provider_fallback_returns_noop():
    provider = get_ai_provider("definitely_not_a_real_provider_123")
    result = provider.improve_text("prompt", "text")
    assert isinstance(result, str)
