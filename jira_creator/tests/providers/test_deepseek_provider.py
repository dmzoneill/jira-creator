#!/usr/bin/env python
"""
Unit tests for the DeepSeekProvider class, specifically targeting the improve_text method. This module contains test
cases that validate the functionality of text improvement, error handling for server issues, and scenarios involving
JSON decoding errors. It employs unittest.mock's MagicMock and patch to simulate various responses from the
improve_text method, ensuring that expected behaviors, method calls, and exception handling are correctly verified. The
tests utilize the pytest framework for assertions and error checking, providing a structured approach to testing the
provider's capabilities and robustness.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError
from providers.deepseek_provider import DeepSeekProvider


@patch("requests.post")
def test_improve_text_success(mock_post):
    """
    Improves text by sending a POST request and receiving a successful response.

    Arguments:
    - mock_post (MagicMock): A MagicMock object representing a POST request.

    Returns:
    - None

    Side Effects:
    - Modifies the behavior of the mock_post object to return a successful response with an improved text message.
    """

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "Improved text"
    }  # Make sure the mock key matches the method's key
    mock_post.return_value = mock_response

    provider = DeepSeekProvider()
    result = provider.improve_text("Fix grammar", "bad grammar sentence")

    # Debugging: Verify the returned result before assertion
    print(
        "Result from improve_text: ", result
    )  # Debugging line to verify returned result

    assert result == "Improved text"
    mock_post.assert_called_once()


@patch("requests.post")
def test_improve_text_failure(mock_post):
    """
    Improves text in case of failure.

    Arguments:
    - mock_post (Mock): A mock object representing a POST request.

    Side Effects:
    - Modifies the text of the mock response to "Internal Server Error" when the status code is 500.
    - Raises AiError with a specific message if the DeepSeek request fails.
    """

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    provider = DeepSeekProvider()
    with pytest.raises(
        AiError, match="DeepSeek request failed: 500 - Internal Server Error"
    ):
        provider.improve_text("Fix grammar", "bad grammar sentence")


@patch("requests.post")
def test_improve_text_json_decode_error(mock_post):
    """
    Simulate a JSON decoding error when processing a response from a mocked POST request.

    Arguments:
    - mock_post: A MagicMock object representing a mocked POST request.

    Exceptions:
    - JSONDecodeError: Raised when there is an issue decoding the JSON response.

    Side Effects:
    - Modifies the behavior of the mock POST request response to simulate an invalid JSON response.
    """

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Invalid JSON"  # Simulate an invalid JSON response
    # Mocking the json method to raise a JSONDecodeError
    mock_response.json.side_effect = json.JSONDecodeError(
        "Expecting value", "Invalid JSON", 0
    )
    mock_post.return_value = mock_response

    provider = DeepSeekProvider()

    # Assert that an exception is raised when the response is not a valid JSON
    with pytest.raises(AiError):
        provider.improve_text("Fix grammar", "bad grammar sentence")
