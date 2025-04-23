"""
This file contains test cases for the search_users function in the CLI module.
The test_cli_search_users_prints_results function tests the successful printing of user search results.
The test_cli_search_users_prints_warning_on_empty function tests the warning message when no users are found.
The test_cli_search_users_raises_on_error function tests the exception handling when an error occurs during the search.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SearchUsersError


def test_cli_search_users_prints_results(cli, capsys):
    """
    Prints the results of searching for users using the CLI.

    Arguments:
    - cli: An object representing the CLI interface.
    - capsys: A pytest fixture for capturing stdout and stderr output.

    """

    cli.jira.search_users = MagicMock()
    cli.jira.search_users.return_value = [
        {
            "name": "daoneill",
            "emailAddress": "daoneill@redhat.com",
            "displayName": "David O'Neill",
        }
    ]

    class Args:
        query = "daoneill"

    cli.search_users(Args())

    out = capsys.readouterr().out
    assert "🔹 User:" in out
    assert "name: daoneill" in out
    assert "displayName: David O'Neill" in out


def test_cli_search_users_prints_warning_on_empty(cli, capsys):
    """
    Search for users using the CLI and print a warning if no users are found.

    Arguments:
    - cli: An object representing the CLI interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Side Effects:
    - Modifies the MagicMock object `cli.jira.search_users` to return an empty list.

    """

    cli.jira.search_users = MagicMock()
    cli.jira.search_users.return_value = []

    class Args:
        query = "unknown-user"

    cli.search_users(Args())

    out = capsys.readouterr().out
    assert "⚠️ No users found." in out


def test_cli_search_users_raises_on_error(cli, capsys):
    """
    This function tests that the CLI search_users function raises an exception when an error occurs during the search.

    Arguments:
    - cli: An object representing the CLI application.
    - capsys: A fixture provided by pytest to capture stdout and stderr outputs.

    Exceptions:
    - SearchUsersError: Raised when an error occurs during the search_users function execution.
    """

    cli.jira.search_users = MagicMock(side_effect=SearchUsersError("API unreachable"))

    class Args:
        query = "error-trigger"

    with pytest.raises(SearchUsersError) as e:
        cli.search_users(Args())

    out = capsys.readouterr().out
    assert "❌ Unable to search users: API unreachable" in out
    assert "API unreachable" in str(e.value)
