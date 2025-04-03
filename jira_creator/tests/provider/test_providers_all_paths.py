from providers import get_ai_provider
from providers.noop_provider import NoAIProvider
import pytest
from unittest.mock import patch


def test_get_ai_provider_openai():
    provider = get_ai_provider("openai")
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_get_ai_provider_gpt4all():
    class FailingGPT4AllProvider:
        def __init__(self):
            raise RuntimeError("simulated failure to load GPT4All")

    with patch("providers.gpt4all_provider.GPT4AllProvider", FailingGPT4AllProvider):
        provider = get_ai_provider("gpt4all")
        assert isinstance(provider, NoAIProvider)


def test_get_ai_provider_instructlab():
    class FailingInstructLab:
        def __init__(self):
            raise Exception("💥 boom")

    with patch("providers.instructlab_provider.InstructLabProvider", FailingInstructLab):
        provider = get_ai_provider("instructlab")
        assert isinstance(provider, NoAIProvider)


def test_get_ai_provider_bart():
    provider = get_ai_provider("bart")
    assert provider.__class__.__name__ == "BARTProvider"


def test_get_ai_provider_deepseek():
    provider = get_ai_provider("deepseek")
    assert provider.__class__.__name__ == "DeepSeekProvider"


def test_import_error():
    def raise_import_error():
        raise ImportError("simulated import error")

    # Patch the constructor of BARTProvider to raise ImportError
    with patch("providers.bart_provider.BARTProvider", raise_import_error):
        provider = get_ai_provider("bart")
        assert isinstance(provider, NoAIProvider)
