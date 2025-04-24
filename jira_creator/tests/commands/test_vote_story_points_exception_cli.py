#!/usr/bin/env python
"""
Test script to validate the behavior of the vote_story_points method in the cli module.

The test simulates an error scenario by mocking the vote_story_points method and raising a VoteStoryPointsError.
It asserts that the error message is present in the output when the method is called with specific arguments.

This script uses pytest for testing and unittest.mock for mocking the method behavior.

Functions:
- test_vote_story_points_error: Simulate an error when voting for story points in Jira. It takes 'cli' (an instance of
the CLI class) and 'capsys' (a fixture provided by pytest to capture stdout and stderr) as arguments. It raises a
VoteStoryPointsError when simulating an error while voting for story points in Jira.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import VoteStoryPointsError


def test_vote_story_points_error(cli, capsys):
    """
    Simulate an error when voting for story points in Jira.

    Arguments:
    - cli: An instance of the CLI class.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Exceptions:
    - VoteStoryPointsError: Raised when simulating an error while voting for story points in Jira.
    """

    # Mock the vote_story_points method to simulate an error
    cli.jira.vote_story_points = MagicMock(side_effect=VoteStoryPointsError("fail"))

    class Args:
        issue_key = "AAP-test_vote_story_points_error"
        points = "8"

    with pytest.raises(VoteStoryPointsError):
        # Call the method and capture the output
        cli.vote_story_points(Args())
    out = capsys.readouterr().out

    # Assert that the error message is in the output
    assert "❌ Failed to vote on story points" in out
