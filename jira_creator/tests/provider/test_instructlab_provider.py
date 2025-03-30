from unittest.mock import MagicMock, patch

import pytest
from providers.instructlab_provider import InstructLabProvider


def test_instructlab_provider_init_defaults(monkeypatch):
    monkeypatch.delenv("INSTRUCTLAB_URL", raising=False)
    monkeypatch.delenv("INSTRUCTLAB_MODEL", raising=False)

    provider = InstructLabProvider()
    assert provider.url == "http://localhost:11434/api/generate"
    assert provider.model == "instructlab"


def test_instructlab_provider_init_env(monkeypatch):
    monkeypatch.setenv("INSTRUCTLAB_URL", "http://custom-url")
    monkeypatch.setenv("INSTRUCTLAB_MODEL", "custom-model")

    provider = InstructLabProvider()
    assert provider.url == "http://custom-url"
    assert provider.model == "custom-model"


def test_improve_text_success(monkeypatch):
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


def test_improve_text_failure(monkeypatch):
    provider = InstructLabProvider()

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    with patch(
        "providers.instructlab_provider.requests.post", return_value=mock_response
    ):
        with pytest.raises(Exception) as exc_info:
            provider.improve_text("Prompt", "Input text")

    assert "InstructLab request failed: 500 - Server error" in str(exc_info.value)
