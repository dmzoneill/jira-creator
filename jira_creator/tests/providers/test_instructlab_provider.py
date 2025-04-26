#!/usr/bin/env python
"""
This module contains unit tests for the InstructLabProvider class from the instructlab_provider module. It verifies the
correct functionality of the provider, including its initialization with default values, and the behavior of the
improve_text method under both successful and failure scenarios.

The tests utilize unittest.mock's MagicMock and patch, alongside pytest for assertions. Key functions include:

- test_instructlab_provider_init_defaults: Tests the initialization of the InstructLabProvider with default values for
URL and model attributes.

- test_improve_text_success: Tests the improve_text method for successful text improvement when the server responds
correctly.

- test_improve_text_failure: Tests the improve_text method's error handling when the server responds with an error
status code.

Overall, this module ensures the robustness of the InstructLabProvider's functionality.
"""

from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError
from providers.instructlab_provider import InstructLabProvider


def test_instructlab_provider_init_defaults():
    """
    Initialize an InstructLabProvider object with default values for url and model attributes.

    Arguments:
    No arguments.

    Return:
    No return value.

    Side Effects:
    Initializes an InstructLabProvider object with url set to "http://some/url" and model set to "hhhhhhhhhhhhh".
    """

    provider = InstructLabProvider()
    assert provider.url == "http://some/url"
    assert provider.model == "hhhhhhhhhhhhh"


def test_improve_text_success():
    """
    Initialize an InstructLabProvider object for testing purposes.
    """

    provider = InstructLabProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": " Improved text "}

    with patch(
        "providers.instructlab_provider.requests.post", return_value=mock_response
    ) as mock_post:
        result = provider.improve_text("Prompt", "Input text")

    assert result == "Improved text"
    mock_post.assert_called_once()
    assert "Prompt\n\nInput text" in mock_post.call_args[1]["json"]["prompt"]


def test_improve_text_failure():
    """
    This function tests the error handling of the improve_text method in the InstructLabProvider class. It initializes
    an instance of the InstructLabProvider class and simulates a server error response during the text improvement
    process. The function raises an AiError exception with a specific error message if the server responds with an HTTP
    status code of 500.
    """

    provider = InstructLabProvider()

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    with patch(
        "providers.instructlab_provider.requests.post", return_value=mock_response
    ):
        with pytest.raises(AiError) as exc_info:
            provider.improve_text("Prompt", "Input text")

    assert "InstructLab request failed: 500 - Server error" in str(exc_info.value)
