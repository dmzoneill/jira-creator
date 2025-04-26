#!/usr/bin/env python
"""
This file contains unit tests for the OpenAIProvider class in the providers.openai_provider module. It includes tests
for the improve_text method, which interacts with the OpenAI API to improve text inputs. The tests cover scenarios
where the API call is successful and when it fails, asserting the expected behavior in each case.

Functions:
- test_openai_provider_improve_text: Tests the OpenAI provider's text improvement functionality by mocking a response
object.
- test_improve_text_raises_on_api_failure: Tests the OpenAIProvider API for text improvement, specifically the GPT-3.5
Turbo model.

Exceptions:
- AiError: Raised if there is a failure when calling the OpenAIProvider API.

Side Effects:
- Modifies the OpenAIProvider instance by setting the API key, model, and endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError
from providers.openai_provider import OpenAIProvider


def test_openai_provider_improve_text():
    """
    This function tests the OpenAI provider's text improvement functionality by mocking a response object with a status
    code of 200 and a JSON payload containing cleaned up text in the "choices" field.

    Arguments:
    - No arguments taken explicitly.

    Return:
    - No explicit return value. The function tests the text improvement functionality by mocking a response object.

    Exceptions:
    - No exceptions raised explicitly in this function.
    """

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
    """
    Improve the text using the OpenAIProvider API, specifically the GPT-3.5 Turbo model.

    Arguments:
    - No arguments.

    Exceptions:
    - Raises an exception if there is a failure when calling the OpenAIProvider API.

    Side Effects:
    - Modifies the OpenAIProvider instance by setting the API key, model, and endpoint.
    """

    provider = OpenAIProvider()
    provider.api_key = "fake-key"
    provider.model = "gpt-3.5-turbo"
    provider.endpoint = "https://api.openai.com/v1/chat/completions"

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("providers.openai_provider.requests.post", return_value=mock_response):
        with pytest.raises(AiError) as exc_info:
            provider.improve_text("test prompt", "test input")

    assert "OpenAI API call failed: 500 - Internal Server Error" in str(exc_info.value)
