#!/usr/bin/env python
"""
This script defines two test functions: test_unassign_success and test_unassign_failure.
Each test function mocks the behavior of unassigning an issue in a Jira system using a lambda function.
The test_unassign_success function simulates a successful unassignment by returning True, while test_unassign_failure
simulates a failed unassignment by returning False.
Both functions then assert the presence of specific output messages in the captured stdout using capsys.
These tests are designed to validate the behavior of the unassign method in the provided CLI implementation.

test_unassign_success:
Unassign an issue in Jira successfully.

Arguments:
- cli: An object representing the command-line interface.
- capsys: A fixture provided by pytest to capture stdout and stderr.

Side Effects:
- Modifies the unassign_issue method of the Jira object in the cli.

test_unassign_failure:
Simulates a failure scenario when trying to unassign an issue in Jira.

Arguments:
- cli: An object representing the CLI.
- capsys: A fixture provided by pytest to capture stdout and stderr outputs.

No return value.

Side Effects:
- Modifies the unassign_issue method of the Jira object to always return False.
"""


def test_unassign_success(cli, capsys):
    """
    Unassign an issue in Jira successfully.

    Arguments:
    - cli: An object representing the command-line interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Side Effects:
    - Modifies the unassign_issue method of the Jira object in the cli.
    """

    cli.jira.unassign_issue = lambda k: True

    class Args:
        issue_key = "AAP-test_unassign_success"

    cli.unassign(Args())
    out = capsys.readouterr().out
    assert "✅" in out


def test_unassign_failure(cli, capsys):
    """
    Simulates a failure scenario when trying to unassign an issue in Jira.

    Arguments:
    - cli: An object representing the CLI.
    - capsys: A fixture provided by pytest to capture stdout and stderr outputs.

    No return value.

    Side Effects:
    - Modifies the unassign_issue method of the Jira object to always return False.
    """

    cli.jira.unassign_issue = lambda k: False

    class Args:
        issue_key = "AAP-test_unassign_failure"

    cli.unassign(Args())
    out = capsys.readouterr().out
    assert "❌" in out
