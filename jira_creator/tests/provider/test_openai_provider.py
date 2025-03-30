from unittest.mock import MagicMock, patch

import pytest
import requests
from providers.openai_provider import OpenAIProvider


def test_openai_provider_improve_text(monkeypatch):
    mock_response = type(
        "Response",
        (),
        {
            "status_code": 200,
            "json": lambda self: {
                "choices": [{"message": {"content": "Cleaned up text"}}]
            },
        },
    )()

    requests.post = lambda *args, **kwargs: mock_response
    provider = OpenAIProvider()
    result = provider.improve_text("fix this", "some bad text")
    assert result == "Cleaned up text"


def test_openai_provider_raises_without_api_key(monkeypatch):
    # Mocking the environment variable being None or missing
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(
        EnvironmentError, match="OPENAI_API_KEY not set in environment."
    ):
        OpenAIProvider()  # This should raise an EnvironmentError


def test_improve_text_raises_on_api_failure(monkeypatch):
    provider = OpenAIProvider()
    provider.api_key = "fake-key"
    provider.model = "gpt-3.5-turbo"
    provider.endpoint = "https://api.openai.com/v1/chat/completions"

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("providers.openai_provider.requests.post", return_value=mock_response):
        with pytest.raises(Exception) as exc_info:
            provider.improve_text("test prompt", "test input")

    assert "OpenAI API call failed: 500 - Internal Server Error" in str(exc_info.value)
