from exceptions.exceptions import AiError


def _try_cleanup(ai_provider, prompt, text):
    """
    Attempts to clean up text using an AI provider.

    Arguments:
    - ai_provider (AiProvider): An AI provider object used to improve text.
    - prompt (str): A prompt or context for the text improvement process.
    - text (str): The text to be cleaned up.

    Return:
    - str: The cleaned up text.

    Exceptions:
    - AiError: If the AI cleanup process fails, an AiError is raised.
    """

    try:
        return ai_provider.improve_text(prompt, text)
    except AiError as e:
        msg = f"⚠️ AI cleanup failed: {e}"
        print(msg)
        raise AiError(msg)
