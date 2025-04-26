#!/usr/bin/env python
"""
This module provides a function to retrieve AI providers based on the specified name. The function takes a name
parameter, which is a string representing the desired AI provider. It attempts to import the corresponding provider
class based on the name and returns an instance of that provider.

If the specified provider is not found or if there is an error during initialization, the function falls back to a
default NoAIProvider and prints a warning message.

The supported AI providers include OpenAI, GPT4All, InstructLab, BART, and DeepSeek. If a provider is not found or if
there is an error, appropriate warning messages are printed.

Note: The module assumes the existence of provider classes like OpenAIProvider, GPT4AllProvider, InstructLabProvider,
BARTProvider, DeepSeekProvider, and NoAIProvider in the respective modules.

Usage:
provider = get_ai_provider("openai")
provider.do_something()

Returns:
An instance of the specified AI provider class or a NoAIProvider instance if the specified provider is not found or if
there is an error during initialization.
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
