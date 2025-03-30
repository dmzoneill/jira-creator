from providers import get_ai_provider


def test_get_ai_provider_noop():
    provider = get_ai_provider("noop")
    assert provider.improve_text("prompt", "text") == "text"


def test_get_ai_provider_fallback():
    provider = get_ai_provider("xyz")
    assert provider.improve_text("prompt", "example") == "example"
