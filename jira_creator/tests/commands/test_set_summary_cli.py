#!/usr/bin/env python
"""
Set a summary for a Jira issue using a mocked CLI.

Arguments:
- cli: A mocked CLI object.
- capsys: A fixture for capturing stdout and stderr outputs.
"""
from unittest.mock import MagicMock


def test_set_summary_ai_fail(cli, capsys):
    """
    Set a summary for a Jira issue using a mocked CLI.

    Arguments:
    - cli: A mocked CLI object.
    - capsys: A fixture for capturing stdout and stderr outputs.
    """

    cli.jira.set_summary = MagicMock()

    class Args:
        issue_key = "AAP-test_set_summary_ai_fail"
        summary = "New Summary"

    cli.set_summary(Args())
