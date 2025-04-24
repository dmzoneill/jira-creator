"""
This file contains unit tests for the InstructLabProvider class from the instructlab_provider module.
It includes tests for initializing the provider with default values, improving text successfully, and handling failure
scenarios.
The tests use MagicMock and patch from the unittest.mock module, as well as pytest for assertions.
The improve_text method of the provider is tested for successful and failed responses from the server.
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
    This function initializes an instance of the InstructLabProvider class for testing purposes.
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
