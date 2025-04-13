from unittest.mock import MagicMock, patch

import pytest
from providers.openai_provider import OpenAIProvider


def test_openai_provider_improve_text():
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

    with patch("providers.openai_provider.requests.post", return_value=mock_response):
        provider = OpenAIProvider()
        result = provider.improve_text("fix this", "some bad text")
        assert result == "Cleaned up text"


def test_improve_text_raises_on_api_failure():
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
