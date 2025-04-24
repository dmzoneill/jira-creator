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


def test_handle_success(cli, capsys):
    """
    Handles the success case for a test scenario.

    Arguments:
    - cli: An object representing the command line interface.
    - capsys: A fixture for capturing stdout and stderr outputs during the test.

    Side Effects:
    - Modifies the 'set_story_epic' attribute of the 'jira' object in the 'cli' object using MagicMock.
    """

    cli.jira.set_story_epic = MagicMock()

    class Args:
        issue_key = "AAP-test_handle_success"
        epic_key = "EPIC-123"

    # Call the handle function
    cli.set_story_epic(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the correct message was printed
    assert "✅ Story's epic set to 'EPIC-123'" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.set_story_epic.assert_called_once_with(
        "AAP-test_handle_success", "EPIC-123"
    )


def test_set_story_epic_exception(cli, capsys):
    """
    Set a side effect for the mock 'set_story_epic' method of the 'cli.jira' object to raise a 'SetStoryEpicError'
    exception with message "fail".
    """

    cli.jira.set_story_epic = MagicMock(side_effect=SetStoryEpicError("fail"))

    class Args:
        issue_key = "AAP-test_set_story_epic_exception"
        epic_key = "EPIC-123"
        reporter = "me"
        project = "aa"
        component = "bb"

    with pytest.raises(SetStoryEpicError):
        # Call the handle function
        cli.set_story_epic(Args())
