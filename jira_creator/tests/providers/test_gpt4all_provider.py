from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import GTP4AllError
from providers.gpt4all_provider import GPT4AllProvider


def test_init_success():
    with patch("providers.gpt4all_provider.GPT4All") as mock_gpt:
        instance = GPT4AllProvider("mock-model")
        assert instance.model_name == "mock-model"
        mock_gpt.assert_called_once_with("mock-model")


def test_init_failure():
    with patch("providers.gpt4all_provider.GPT4All", side_effect=GTP4AllError("💥")):
        with pytest.raises(GTP4AllError, match="Failed to load GPT4All model: 💥"):
            GPT4AllProvider("broken-model")


def test_improve_text():
    mock_model = MagicMock()
    mock_model.generate.return_value = " improved text "

    with patch("providers.gpt4all_provider.GPT4All", return_value=mock_model):
        provider = GPT4AllProvider("mock-model")
        result = provider.improve_text("Prompt", "Original text")

        assert "Prompt" in mock_model.generate.call_args[0][0]
        assert "Original text" in mock_model.generate.call_args[0][0]
        assert result == "improved text"
