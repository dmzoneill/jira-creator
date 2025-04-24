#!/usr/bin/env python
"""
This file contains test functions for the 'assign' method in a CLI tool.
The 'test_assign_success' function tests the successful assignment of an issue using a mock Jira client, while the
'test_assign_failure' function tests the failure scenario.
Each test function sets up a mock Jira client behavior, invokes the 'assign' method with specific arguments, captures
the output, and asserts the expected output message.

test_assign_success(cli, capsys):
Assign a success test for the assign_issue method in the Jira CLI.

Arguments:
- cli: An instance of the Jira CLI.
- capsys: Pytest fixture for capturing stdout and stderr output.

Side Effects:
- Modifies the assign_issue method in the Jira CLI to always return True.

test_assign_failure(cli, capsys):
Assign a failure status to a Jira issue using a mock CLI.

Arguments:
- cli: An object representing the CLI (Command Line Interface).
- capsys: A fixture provided by pytest to capture stdout and stderr.

Exceptions:
- None

Side Effects:
- Modifies the assign_issue method of the cli.jira object to always return False.
"""


def test_assign_success(cli, capsys):
    """
    Assign a success test for the assign_issue method in the Jira CLI.

    Arguments:
    - cli: An instance of the Jira CLI.
    - capsys: Pytest fixture for capturing stdout and stderr output.

    Side Effects:
    - Modifies the assign_issue method in the Jira CLI to always return True.
    """

    cli.jira.assign_issue = lambda k, a: True

    class Args:
        issue_key = "AAP-test_assign_success"
        assignee = "johndoe"

    cli.assign(Args())
    out = capsys.readouterr().out
    assert "✅ assigned AAP-test_assign_success to johndoe" in out


def test_assign_failure(cli, capsys):
    """
    Assign a failure status to a Jira issue using a mock CLI.

    Arguments:
    - cli: An object representing the CLI (Command Line Interface).
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Exceptions:
    - None

    Side Effects:
    - Modifies the assign_issue method of the cli.jira object to always return False.
    """

    cli.jira.assign_issue = lambda k, a: False

    class Args:
        issue_key = "AAP-test_assign_failure"
        assignee = "johndoe"

    cli.assign(Args())
    out = capsys.readouterr().out
    assert "❌ Could not assign AAP-test_assign_failure to johndoe" in out
