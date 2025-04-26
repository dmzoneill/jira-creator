#!/usr/bin/env python
"""
This file contains unit tests for the view_user function in the CLI module.
It includes tests for printing user fields and handling GetUserError exceptions.
Mock objects are used to simulate interactions with the Jira API.
The test_cli_view_user_prints_user_fields test verifies that user fields are correctly printed.
The test_cli_view_user_raises_and_prints_error test checks if GetUserError exceptions are raised and handled
appropriately.
pytest and unittest.mock libraries are imported for testing purposes.

Functions:
- test_cli_view_user_prints_user_fields(cli, capsys): Prints user fields for a specific user using the CLI.
- test_cli_view_user_raises_and_prints_error(cli, capsys): Tests the CLI view user functionality by simulating a
scenario where an error is raised when attempting to get user information from Jira.

Arguments:
- cli: An object representing the CLI.
- capsys: A fixture provided by pytest to capture stdout and stderr.

Exceptions:
- GetUserError: Raised when the simulated scenario encounters an error message "User not found".
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import GetUserError


def test_cli_view_user_prints_user_fields(cli, capsys):
    """
    Prints user fields for a specific user using the CLI.

    Arguments:
    - cli: An object representing the CLI.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Side Effects:
    - Prints the user fields for a specific user to the standard output.
    """

    cli.jira.get_user = MagicMock()
    cli.jira.get_user.return_value = {
        "accountId": "abc123",
        "displayName": "David O'Neill",
        "emailAddress": "daoneill@redhat.com",
    }

    class Args:
        account_id = "abc123"

    cli.view_user(Args())

    out = capsys.readouterr().out
    assert "accountId" in out
    assert "displayName" in out
    assert "emailAddress" in out


def test_cli_view_user_raises_and_prints_error(cli, capsys):
    """
    Summary:
    This function tests the CLI view user functionality by simulating a scenario where an error is raised when
    attempting to get user information from Jira.

    Arguments:
    - cli: An instance of the CLI class that provides Jira functionality.
    - capsys: A pytest fixture to capture stdout and stderr output.

    Exceptions:
    - GetUserError: Raised when the simulated scenario encounters an error message "User not found".
    """

    cli.jira.get_user = MagicMock()
    cli.jira.get_user.side_effect = GetUserError("User not found")

    class Args:
        account_id = "notreal"

    with pytest.raises(GetUserError) as e:
        cli.view_user(Args())

    out = capsys.readouterr().out
    assert "❌ Unable to retrieve user: User not found" in out
    assert "User not found" in str(e.value)
