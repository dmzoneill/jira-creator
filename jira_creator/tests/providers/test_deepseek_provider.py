import json
from unittest.mock import MagicMock, patch

import pytest
from providers.deepseek_provider import DeepSeekProvider


@patch("requests.post")
def test_improve_text_success(mock_post):
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
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    provider = DeepSeekProvider()
    with pytest.raises(
        Exception, match="DeepSeek request failed: 500 - Internal Server Error"
    ):
        provider.improve_text("Fix grammar", "bad grammar sentence")


@patch("requests.post")
def test_improve_text_json_decode_error(mock_post):
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
    with pytest.raises(Exception, match="Failed to parse response: Invalid JSON"):
        provider.improve_text("Fix grammar", "bad grammar sentence")
