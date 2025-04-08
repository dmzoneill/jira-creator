from exceptions.exceptions import AiProviderError


def get_ai_provider(name: str):
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
        raise (AiProviderError(msg))

    from .noop_provider import NoAIProvider

    print("⚠️ Falling back to NoAIProvider.")
    return NoAIProvider()
