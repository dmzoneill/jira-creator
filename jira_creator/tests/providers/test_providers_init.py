from providers import get_ai_provider


def test_get_ai_provider_noop():
    """
    Get the AI provider for a specific type and test its functionality with a "noop" provider.

    Arguments:
    - provider (str): The type of AI provider to retrieve. In this case, it is set to "noop".

    Return:
    - None

    """

    provider = get_ai_provider("noop")
    assert provider.improve_text("prompt", "text") == "text"


def test_get_ai_provider_fallback():
    """
    Summary:
    Test function to verify the fallback behavior of an AI provider when a specific provider is not available.

    Arguments:
    - No arguments are passed to the function.

    Return:
    - No return value.

    """

    provider = get_ai_provider("xyz")
    assert provider.improve_text("prompt", "example") == "example"
