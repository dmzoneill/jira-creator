#!/usr/bin/env python
"""
Simulates an error scenario by mocking the AI provider's improve_text method.

Arguments:
- cli: An instance of the CLI class.

Exceptions:
- AiError: Raised when the improve_text method of the AI provider encounters an error.
"""
from unittest.mock import MagicMock

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
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = AiError("fail")

    with pytest.raises(AiError):
        # Call _try_cleanup and assert the result
        cli._try_cleanup("prompt", "text")
