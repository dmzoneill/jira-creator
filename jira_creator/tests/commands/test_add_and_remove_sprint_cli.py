#!/usr/bin/env python
"""
This script defines unit tests for the 'add_sprint' and 'remove_sprint' functions in the 'cli' module.
The tests use MagicMock to mock certain functionalities.
Each test creates an 'Args' class instance with specific attributes and then calls the corresponding function in the
'cli' module.
The tests verify that the expected functions from the 'cli.jira' object are called once.

Functions:
- test_add_to_sprint(cli): Adds a sprint to a Jira board using the provided CLI.
- test_remove_sprint(cli): Remove a JIRA issue from the current sprint.
"""

from unittest.mock import MagicMock


def test_add_sprint(cli):
    """
    Adds a sprint to a Jira board using the provided CLI.

    Arguments:
    - cli (object): An instance of the CLI object used to interact with Jira.

    Side Effects:
    - Modifies the 'add_to_sprint' attribute of the 'cli.jira' object by replacing it with a MagicMock object.
    """

    cli.jira.add_to_sprint = MagicMock()

    class Args:
        issue_key = "AAP-test_add_to_sprint"
        sprint_name = "Sprint 1"
        assignee = "user1"

    cli.add_to_sprint(Args())
    cli.jira.add_to_sprint.assert_called_once()


def test_remove_from_sprint(cli):
    """
    Remove a JIRA issue from the current sprint.

    Arguments:
    - cli: An object representing the command-line interface.

    Side Effects:
    - Modifies the 'remove_from_sprint' attribute of the 'jira' object in the 'cli' object.
    """

    cli.jira.remove_from_sprint = MagicMock()

    class Args:
        issue_key = "AAP-test_remove_from_sprint"

    cli.remove_sprint(Args())
    cli.jira.remove_from_sprint.assert_called_once()
