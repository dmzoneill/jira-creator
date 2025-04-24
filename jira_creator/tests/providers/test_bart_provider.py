#!/usr/bin/env python
"""
This file contains unit tests for the BARTProvider class in the bart_provider module.
It includes tests for the initialization of the BARTProvider, successful and failed text improvement scenarios.
The tests use mock objects and patches to simulate HTTP requests and responses.

Functions:
- test_bart_provider_init(): Initialize a BARTProvider object with a default URL and headers for BART API requests.
- test_improve_text_success(mock_post): Improves the text by sending a mock POST request.
- test_improve_text_failure(mock_post): Improves the text of a failed post request response.
"""

from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError
from providers.bart_provider import BARTProvider


def test_bart_provider_init():
    """
    Initialize a BARTProvider object with a default URL and headers for BART API requests.

    Arguments:
    No arguments.

    Returns:
    No return value.

    Exceptions:
    No exceptions raised.
    """

    provider = BARTProvider()
    assert provider.url == "http://some/url"
    assert provider.headers == {"Content-Type": "application/json"}


@patch("providers.bart_provider.requests.post")
def test_improve_text_success(mock_post):
    """
    Improves the text by sending a mock POST request.

    Arguments:
    - mock_post (MagicMock): A mock object representing a POST request function.

    Side Effects:
    - Modifies the mock_post function to return a mock response with status code 200 and JSON data {"output": "Improved
    text"}.
    """

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"output": "Improved text"}
    mock_post.return_value = mock_response

    provider = BARTProvider()
    result = provider.improve_text("Improve this", "Bad text")
    assert result == "Improved text"
    mock_post.assert_called_once()


@patch("providers.bart_provider.requests.post")
def test_improve_text_failure(mock_post):
    """
    Improves the text of a failed post request response.

    Arguments:
    - mock_post (MagicMock): A MagicMock object representing the post request function.

    Side Effects:
    - Modifies the text of the response to "Internal Server Error" and sets the status code to 500.
    """

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    provider = BARTProvider()
    with pytest.raises(
        AiError, match="BART request failed: 500 - Internal Server Error"
    ):
        provider.improve_text("Prompt", "Text")
