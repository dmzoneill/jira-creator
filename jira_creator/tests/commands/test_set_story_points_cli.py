#!/usr/bin/env python
"""
Unit tests for the 'set_story_points' function in the 'cli' module.

This module includes tests to verify the functionality of setting story points for Jira issues through the command line
interface (CLI). It covers various scenarios including successful setting of story points, handling of exceptions, and
validation of input values.

Key Features:
- Tests for successful story point assignment.
- Tests for failure cases using mocked methods.
- Validation of input types to ensure correct data types are used.
- Utilizes pytest for testing framework and assertions.
- Implements MagicMock for mocking dependencies.

Exceptions tested:
- SetStoryPointsError: Raised during failure scenarios when setting story points fails.
- ValueError: Raised when an invalid non-integer value is provided for story points.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetStoryPointsError


def test_set_story_points_success(cli):
    """
    Set story points for a Jira issue using the CLI.

    Arguments:
    - cli: An object representing the CLI interface.

    Side Effects:
    - Modifies the 'jira' attribute of the 'cli' object by setting the 'set_story_points' attribute to a MagicMock
    object.
    """

    mock_set_story_points = MagicMock()
    cli.jira = MagicMock(set_story_points=mock_set_story_points)

    class Args:
        issue_key = "AAP-test_set_story_points_success"
        points = 5

    cli.set_story_points(Args())
    mock_set_story_points.assert_called_once_with(
        "AAP-test_set_story_points_success", 5
    )


def test_set_story_points_failure(cli, capsys):
    """
    Set the story points for a test case and handle failure scenarios.

    Arguments:
    - cli (CommandLineInterface): An instance of the CommandLineInterface class used for interacting with the command
    line.
    - capsys (CaptureFixture): Pytest fixture for capturing stdout and stderr output.

    Exceptions:
    - No explicit exceptions are raised within this function.

    Side Effects:
    - This function interacts with the command line interface (cli) to set story points for a test case.
    - It may output information to stdout or stderr using the capsys fixture.

    Note: This function likely handles the scenario where setting story points for a test case fails.
    """

    def boom(issue_key, points):
        """
        Set the story points for a specific issue identified by the provided issue key.

        Arguments:
        - issue_key (str): A string representing the unique key of the issue.
        - points (int): An integer indicating the story points to be set for the issue.

        Exceptions:
        - SetStoryPointsError: Raised when there is a failure in setting the story points for the issue.

        Side Effects:
        Raises a SetStoryPointsError exception with a message indicating a fake failure.
        """

        raise SetStoryPointsError("fake failure")

    cli.jira = MagicMock(set_story_points=boom)

    class Args:
        issue_key = "AAP-test_set_story_points_failure"
        points = 5

    with pytest.raises(SetStoryPointsError):
        cli.set_story_points(Args())

    captured = capsys.readouterr()
    assert "❌ Failed to set story points" in captured.out


def test_set_story_points_value_error(cli, capsys):
    """
    Set story points for an issue identified by the given key.

    Arguments:
    - cli: An instance of the command-line interface.
    - capsys: An object capturing stdout and stderr outputs.

    Exceptions:
    - ValueError: Raised when the points parameter is not a valid integer.

    Side Effects:
    None
    """

    class Args:
        issue_key = "AAP-test_set_story_points_value_error"
        points = "five"  # invalid non-integer value

    cli.set_story_points(Args())

    captured = capsys.readouterr()
    assert "❌ Points must be an integer." in captured.out
