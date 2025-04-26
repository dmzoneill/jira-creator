#!/usr/bin/env python
"""
This script defines a function '_try_cleanup' that attempts to clean up text using an AI provider.

The function takes three arguments:
- ai_provider (AiProvider): An AI provider object used to improve text.
- prompt (str): A prompt or context for the text improvement process.
- text (str): The text to be cleaned up.

It returns:
- str: The cleaned up text.

It raises an AiError exception if the AI cleanup process fails.
"""
from exceptions.exceptions import AiError
from providers.ai_provider import AIProvider


def _try_cleanup(ai_provider: AIProvider, prompt: str, text: str) -> str:
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
        raise AiError(e) from e
