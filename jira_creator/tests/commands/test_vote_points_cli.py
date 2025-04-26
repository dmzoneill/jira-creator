#!/usr/bin/env python
"""
Simulate voting for story points in Jira using the provided CLI and capsys fixtures.

This file contains a test function to simulate the process of voting for story points in Jira. It utilizes fixtures
representing the command-line interface for Jira (cli) and fixtures capturing stdout and stderr output (capsys).

Args:
- cli: A fixture representing the command-line interface for Jira.
- capsys: A fixture capturing stdout and stderr output.

Side Effects:
- Modifies the vote_story_points attribute of the cli.jira object using MagicMock.
"""
from unittest.mock import MagicMock


def test_vote_story_points(cli, capsys):
    """
    Simulate voting for story points in Jira using the provided CLI and capsys fixtures.
    Args:
    cli: A fixture representing the command-line interface for Jira.
    capsys: A fixture capturing stdout and stderr output.

    Side Effects:
    - Modifies the vote_story_points attribute of the cli.jira object using MagicMock.
    """

    cli.jira.vote_story_points = MagicMock()

    class Args:
        issue_key = "AAP-test_vote_story_points"
        points = "8"

    cli.vote_story_points(Args())
    cli.jira.vote_story_points.assert_called_once_with("AAP-test_vote_story_points", 8)
    out = capsys.readouterr().out
    assert "✅ Voted" in out
