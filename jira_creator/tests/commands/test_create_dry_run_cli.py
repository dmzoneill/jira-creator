#!/usr/bin/env python
"""
This file contains unit tests for the create_issue function in the CLI module.
It includes test cases for creating an issue in dry run mode and for handling exceptions during issue creation.
Mock objects are used to simulate interactions with the Jira API and user inputs.
The test_create_dry_run function tests the creation of an issue in dry run mode by mocking Jira API calls and user
input.
The test_create_issue_with_exception function tests the handling of exceptions during issue creation by mocking a
CreateIssueError.
Both test cases utilize the pytest framework for assertions and mock objects for simulating behavior.
"""

from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import CreateIssueError


def test_create_dry_run(cli):
    """
    Set up a mock AI provider for testing purposes.

    Arguments:
    - cli: An object representing the command line interface.

    Side Effects:
    - Modifies the `ai_provider` attribute of the `cli` object by assigning a MagicMock object to it.
    """

    cli.ai_provider = MagicMock()

    # Mock method: build_payload returns a payload with summary
    cli.jira.build_payload = lambda s, d, t: {"fields": {"summary": s}}

    # Mock create_issue to just return a fake issue key
    cli.jira.create_issue = lambda payload: "AAP-test_create_dry_run"

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = True

    # Mock input to avoid blocking
    with patch("builtins.input", return_value="Test"):
        cli.create_issue(Args())


def test_create_issue_with_exception(cli):
    """
    Set up a mock AI provider for the CLI to create an issue with an exception.

    Arguments:
    - cli: An instance of the CLI class that will be used to create an issue with an exception.

    Side Effects:
    - Modifies the 'ai_provider' attribute of the provided 'cli' instance by setting it to a MagicMock object.
    """

    cli.ai_provider = MagicMock()

    # Mock method: build_payload returns a payload with summary
    cli.jira.build_payload = lambda s, d, t: {"fields": {"summary": s}}

    # Mock create_issue to raise an exception
    cli.jira.create_issue = MagicMock(
        side_effect=CreateIssueError("Failed to create issue")
    )

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = False

    # Mock input to avoid blocking
    with patch("builtins.input", return_value="Test"):
        # This should raise the exception
        with pytest.raises(CreateIssueError):
            cli.create_issue(Args())
