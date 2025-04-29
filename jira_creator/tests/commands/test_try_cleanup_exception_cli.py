#!/usr/bin/env python
"""
Simulates an error scenario by mocking the AI provider's improve_text method.

Arguments:
- cli: An instance of the CLI class.

Exceptions:
- AiError: Raised when the improve_text method of the AI provider encounters an error.
"""
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError


def test_try_cleanup_error(cli):
    """
    Simulates an error scenario by mocking the AI provider's improve_text method.

    Arguments:
    - cli: An instance of the CLI class.

    Exceptions:
    - AiError: Raised when the improve_text method of the AI provider encounters an error.
    """

    # Mock the AI provider's improve_text method to simulate an exception
    with patch("commands._try_cleanup.get_ai_provider") as mock_get_ai_provider:
        # Create a mock AI provider
        mock_ai_provider = MagicMock()
        mock_ai_provider.improve_text.side_effect = AiError("fail")
        mock_get_ai_provider.return_value = mock_ai_provider

        with pytest.raises(AiError):
            # Call _try_cleanup and assert the result
            cli._try_cleanup("prompt", "text")
