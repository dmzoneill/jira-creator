from unittest.mock import MagicMock, patch

import pytest
from providers.bart_provider import BARTProvider


def test_bart_provider_init():
    provider = BARTProvider()
    assert provider.url == "http://some/url"
    assert provider.headers == {"Content-Type": "application/json"}


@patch("providers.bart_provider.requests.post")
def test_improve_text_success(mock_post):
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
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    provider = BARTProvider()
    with pytest.raises(
        Exception, match="BART request failed: 500 - Internal Server Error"
    ):
        provider.improve_text("Prompt", "Text")
