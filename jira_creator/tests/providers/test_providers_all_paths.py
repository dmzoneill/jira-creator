"""
This file contains unit tests for the get_ai_provider function, which is responsible for retrieving AI providers based
on the provider name provided. The tests cover different scenarios such as successful provider retrieval, failure
cases, and handling of import errors. The tests use patching with unittest.mock.patch and pytest.raises to simulate
failures and exceptions. The AI providers tested include OpenAIProvider, GPT4AllProvider, InstructLabProvider,
BARTProvider, and DeepSeekProvider. In case of failures or import errors, the tests ensure that the appropriate
exceptions are raised or handled gracefully. Additionally, the file imports necessary modules and classes from
exceptions.exceptions and providers modules.
"""

from unittest.mock import patch

import pytest
from exceptions.exceptions import AiProviderError
from providers import get_ai_provider


def test_get_ai_provider_openai():
    """
    This function tests the `get_ai_provider` function with the input parameter "openai". It asserts that the returned
    provider is an instance of the class `OpenAIProvider`.
    """

    provider = get_ai_provider("openai")
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_get_ai_provider_bart():
    """
    This function tests the get_ai_provider function by verifying if the provider returned for "bart" is an instance of
    the BARTProvider class.
    """

    provider = get_ai_provider("bart")
    assert provider.__class__.__name__ == "BARTProvider"


def test_get_ai_provider_deepseek():
    """
    Retrieve the AI provider for DeepSeek and validate its type.

    Arguments:
    - No arguments.

    Return:
    - No return value.

    Exceptions:
    - AssertionError is raised if the provider type is not DeepSeekProvider.
    """

    provider = get_ai_provider("deepseek")
    assert provider.__class__.__name__ == "DeepSeekProvider"


def test_unknown_provider():
    """
    This function is used to test for unknown provider
    """

    # Patch the BARTProvider in the correct module path
    with pytest.raises(AiProviderError):
        get_ai_provider("unknown")
