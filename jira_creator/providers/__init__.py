#!/usr/bin/env python
"""
This module provides functionality to retrieve instances of various AI providers based on a specified name.

The primary function, `get_ai_provider`, takes a string parameter representing the desired AI provider's name and
attempts to return an instance of the corresponding provider class. Supported providers include OpenAI, GPT4All,
InstructLab, BART, and DeepSeek. If the specified provider cannot be found or if an error occurs during initialization,
the function will print a warning message and raise an `AiProviderError`, falling back to a default `NoAIProvider`.

Usage example:
provider = get_ai_provider("openai")
provider.do_something()

Returns:
An instance of the specified AI provider class or raises an `AiProviderError` if the provider is unsupported or
initialization fails.

Exceptions:
- AiProviderError: Raised for unsupported providers or initialization errors.
"""

from typing import Type, Union

from exceptions.exceptions import AiProviderError

from .bart_provider import BARTProvider
from .deepseek_provider import DeepSeekProvider
from .gpt4all_provider import GPT4AllProvider
from .instructlab_provider import InstructLabProvider
from .openai_provider import OpenAIProvider


def get_ai_provider(
    name: str,
) -> Union[
    OpenAIProvider, GPT4AllProvider, InstructLabProvider, BARTProvider, DeepSeekProvider
]:
    """
    Converts the input name to lowercase and returns the corresponding AI provider.

    Arguments:
    - name (str): A string representing the name of an AI provider.

    Returns:
    - An instance of the specified AI provider class or a NoAIProvider instance if the specified provider is not found
    or if there is an error during initialization.

    Exceptions:
    - AiProviderError: Raised if the specified provider is not supported or if there is an error during initialization.

    Side Effects:
    - May print a warning message if there is a failure to load the provider.
    """
    name = name.lower()

    # Map the provider name to the corresponding class
    provider_map: dict[
        str,
        Type[
            Union[
                OpenAIProvider,
                GPT4AllProvider,
                InstructLabProvider,
                BARTProvider,
                DeepSeekProvider,
            ]
        ],
    ] = {
        "openai": OpenAIProvider,
        "gpt4all": GPT4AllProvider,
        "instructlab": InstructLabProvider,
        "bart": BARTProvider,
        "deepseek": DeepSeekProvider,
    }

    try:
        # Look up the provider by name and return an instance
        if name in provider_map:
            provider_class = provider_map[name]
            return provider_class()
        raise AiProviderError(f"Unsupported provider: {name}")
    except (ImportError, AiProviderError) as e:
        print(f"⚠️ Failed to load provider {name}: {e}")
        raise AiProviderError(e) from e
