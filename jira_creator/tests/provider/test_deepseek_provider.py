from unittest.mock import MagicMock, patch

import pytest
from providers.deepseek_provider import DeepSeekProvider


@patch("requests.post")
def test_improve_text_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"output": "Improved text"}
    mock_post.return_value = mock_response

    provider = DeepSeekProvider()
    result = provider.improve_text("Fix grammar", "bad grammar sentence")
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
