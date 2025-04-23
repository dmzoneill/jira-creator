from providers import get_ai_provider


def test_get_ai_provider_fallback_returns_noop():
    """
    This function tests the fallback behavior of the get_ai_provider function when an invalid provider name is
    provided. It verifies that the returned provider object implements the improve_text method and returns a string
    result.
    """

    provider = get_ai_provider("definitely_not_a_real_provider_123")
    result = provider.improve_text("prompt", "text")
    assert isinstance(result, str)
