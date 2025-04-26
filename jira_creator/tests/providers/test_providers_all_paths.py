#!/usr/bin/env python
"""
This file contains unit tests for the get_ai_provider function, which retrieves AI providers based on the provider name
provided. The tests cover scenarios such as successful provider retrieval, failure cases, and handling of import errors
using patching with unittest.mock.patch and pytest.raises. The tested AI providers include OpenAIProvider,
GPT4AllProvider, InstructLabProvider, BARTProvider, and DeepSeekProvider. The tests verify that the appropriate
exceptions are raised or handled gracefully. The file imports modules and classes from exceptions.exceptions and
providers modules.

Test functions like test_get_ai_provider_openai, test_get_ai_provider_bart, test_get_ai_provider_deepseek, and
test_unknown_provider verify the behavior of get_ai_provider for different provider names. Each function asserts that
the returned provider matches the expected provider class. The test_unknown_provider function checks for an
AiProviderError when an unknown provider name is provided.
"""

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

    Exceptions:
    - AssertionError is raised if the provider type is not DeepSeekProvider.
    """

    provider = get_ai_provider("deepseek")
    assert provider.__class__.__name__ == "DeepSeekProvider"


def test_unknown_provider():
    """
    This function is used to test for an unknown provider by attempting to retrieve an AI provider with an unknown name.
    It uses pytest to check if an AiProviderError is raised when attempting to get the AI provider with the name
    "unknown".

    Arguments:
    No arguments are passed to this function.

    Exceptions:
    Raises an AiProviderError if attempting to get an AI provider with the name "unknown" results in an error.

    Side Effects:
    This function interacts with pytest to perform the test for an unknown provider.
    """

    # Patch the BARTProvider in the correct module path
    with pytest.raises(AiProviderError):
        get_ai_provider("unknown")
