from providers.noop_provider import NoAIProvider


def test_noop_provider_returns_original_text():
    """
    Summary:
    Initialize a NoAIProvider object and test that it returns the original text without any modifications.

    Arguments:
    - No arguments.

    Return:
    No return value.

    """

    provider = NoAIProvider()
    prompt = "Improve this text"
    original_text = "This is teh original text with a typo."

    result = provider.improve_text(prompt, original_text)

    assert result == original_text
