#!/usr/bin/env python
"""
Mocks the 'clone_issue' method in the 'cli.jira' object for testing purposes.

Arguments:
- cli: An object representing the CLI (Command Line Interface).
- capsys: A fixture provided by pytest to capture stdout and stderr outputs during testing.
"""
from unittest.mock import MagicMock


def test_clone_issue_ai_fail(cli, capsys):
    """
    Mocks the 'clone_issue' method in the 'cli.jira' object for testing purposes.

    Arguments:
    - cli: An object representing the CLI (Command Line Interface).
    - capsys: A fixture provided by pytest to capture stdout and stderr outputs during testing.
    """

    # Mock the clone_issue method
    cli.jira.clone_issue = MagicMock()

    class Args:
        issue_key = "AAP-test_clone_issue_ai_fail"

    cli.clone_issue(Args())
