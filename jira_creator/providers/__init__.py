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

from exceptions.exceptions import AiProviderError


def get_ai_provider(name: str):
    """
    Converts the input name to lowercase.

    Arguments:
    - name (str): A string representing the name of an AI provider.

    """

    name = name.lower()

    try:
        if name == "openai":
            from .openai_provider import OpenAIProvider

            return OpenAIProvider()
        elif name == "gpt4all":
            from .gpt4all_provider import GPT4AllProvider

            return GPT4AllProvider()
        elif name == "instructlab":
            from .instructlab_provider import InstructLabProvider

            return InstructLabProvider()
        elif name == "bart":
            from .bart_provider import BARTProvider

            return BARTProvider()
        elif name == "deepseek":
            from .deepseek_provider import DeepSeekProvider

            return DeepSeekProvider()
    except ImportError as e:
        print(f"⚠️ Could not import {name} provider: {e}")
    except AiProviderError as e:
        msg = f"⚠️ Failed to initialize {name} provider: {e}"
        print(AiProviderError)
        raise AiProviderError(msg)

    from .noop_provider import NoAIProvider

    print("⚠️ Falling back to NoAIProvider.")
    return NoAIProvider()
