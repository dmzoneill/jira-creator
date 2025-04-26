#!/usr/bin/env python
"""
This file contains unit tests for the set_story_epic function in the CLI module.

The test_handle_success function tests the successful execution of set_story_epic by mocking the JIRA set_story_epic
method and asserting the correct message output and function call arguments.

The test_set_story_epic_exception function tests the handling of SetStoryEpicError exception by mocking the JIRA
set_story_epic method with a side effect and ensuring the exception is raised.

Both test functions utilize the pytest framework and mock objects for testing the CLI module functionality.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetStoryEpicError


def test_cli_set_story_epic_success(cli, capsys):
    """
    Tests the successful case where the epic is set for a story.
    """

    # Mock the set_story_epic method
    cli.jira.set_story_epic = MagicMock(return_value=None)

    # Mock the improve_text method (if needed)
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-12345"
        epic_key = "EPIC-67890"

    # Call the cli_set_story_epic method
    result = cli.set_story_epic(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the result is True
    assert result is True

    # Check that the correct success message is printed
    assert "✅ Story's epic set to 'EPIC-67890'" in out


def test_cli_set_story_epic_missing_argument(cli):
    """
    Tests the case where the required arguments (issue_key, epic_key) are missing.
    """

    class Args:
        # Missing epic_key
        issue_key = "AAP-12345"

    # Expecting a ValueError due to missing epic_key
    with pytest.raises(ValueError):
        cli.set_story_epic(Args())


def test_cli_set_story_epic_invalid_argument_type(cli):
    """
    Tests the case where the arguments are of the wrong type (not strings).
    """

    class Args:
        issue_key = 12345  # Invalid type (not a string)
        epic_key = "EPIC-67890"

    # Expecting a TypeError due to invalid issue_key type
    with pytest.raises(TypeError):
        cli.set_story_epic(Args())


def test_cli_set_story_epic_invalid_epic_key_type(cli):
    """
    Tests the case where the epic_key is not a string.
    """

    class Args:
        issue_key = "AAP-12345"
        epic_key = 67890  # Invalid type (not a string)

    # Expecting a TypeError due to invalid epic_key type
    with pytest.raises(TypeError):
        cli.set_story_epic(Args())


def test_cli_set_story_epic_set_error(cli, capsys):
    """
    Tests the case where the SetStoryEpicError is raised while setting the epic.
    """

    # Mock the set_story_epic method to raise SetStoryEpicError
    cli.jira.set_story_epic = MagicMock(
        side_effect=SetStoryEpicError("Failed to set epic")
    )

    # Mock the improve_text method (if needed)
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-12345"
        epic_key = "EPIC-67890"

    # Call the cli_set_story_epic method and handle the exception
    with pytest.raises(SetStoryEpicError):
        cli.set_story_epic(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the correct error message is printed
    assert "❌ Failed to set epic for issue 'AAP-12345'" in out


def test_cli_set_story_epic_unexpected_error(cli, capsys):
    """
    Tests the case where an unexpected error occurs while setting the epic.
    """

    # Mock the set_story_epic method to raise an unexpected error
    cli.jira.set_story_epic = MagicMock(side_effect=Exception("Unexpected error"))

    # Mock the improve_text method (if needed)
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-12345"
        epic_key = "EPIC-67890"

    # Call the cli_set_story_epic method and handle the exception
    with pytest.raises(RuntimeError):
        cli.set_story_epic(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the correct error message is printed for unexpected error
    assert "❌ An unexpected error occurred" in out
