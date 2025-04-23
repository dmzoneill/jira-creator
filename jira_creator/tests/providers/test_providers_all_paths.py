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
from providers.noop_provider import NoAIProvider


def test_get_ai_provider_openai():
    """
    This function tests the `get_ai_provider` function with the input parameter "openai". It asserts that the returned
    provider is an instance of the class `OpenAIProvider`.
    """

    provider = get_ai_provider("openai")
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_get_ai_provider_gpt4all():
    """
    This function defines a test case for the GPT4All AI provider by creating a mock class called
    FailingGPT4AllProvider.
    """

    class FailingGPT4AllProvider:
        def __init__(self):
            """
            Initialize the AiProviderError by raising an exception indicating a simulated failure to load GPT4All.
            """

            raise AiProviderError("simulated failure to load GPT4All")

    with patch("providers.gpt4all_provider.GPT4AllProvider", FailingGPT4AllProvider):
        with pytest.raises(AiProviderError):
            get_ai_provider("gpt4all")


def test_get_ai_provider_instructlab():
    """
    This function defines a class named FailingInstructLab.
    """

    class FailingInstructLab:
        def __init__(self):
            """
            Initialize the AiProviderError exception.

            Arguments:
            - self: the instance of the class.

            Exceptions:
            - AiProviderError: an exception raised with the message "💥 boom".
            """

            raise AiProviderError("💥 boom")

    with patch(
        "providers.instructlab_provider.InstructLabProvider", FailingInstructLab
    ):
        with pytest.raises(AiProviderError):
            get_ai_provider("instructlab")


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


def test_import_error():
    """
    This function is used to test the behavior of Python when an ImportError occurs during import of a module.
    """

    def raise_import_error():
        """
        Raises an ImportError with a message "simulated import error".
        """

        raise ImportError("simulated import error")

    # Patch the constructor of BARTProvider to raise ImportError
    with patch("providers.bart_provider.BARTProvider", raise_import_error):
        provider = get_ai_provider("bart")
        assert isinstance(provider, NoAIProvider)
