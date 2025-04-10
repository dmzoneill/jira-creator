from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SearchUsersError


def test_cli_search_users_prints_results(cli, capsys):
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
    cli.jira.search_users = MagicMock()
    cli.jira.search_users.return_value = []

    class Args:
        query = "unknown-user"

    cli.search_users(Args())

    out = capsys.readouterr().out
    assert "⚠️ No users found." in out


def test_cli_search_users_raises_on_error(cli, capsys):
    cli.jira.search_users = MagicMock(side_effect=SearchUsersError("API unreachable"))

    class Args:
        query = "error-trigger"

    with pytest.raises(SearchUsersError) as e:
        cli.search_users(Args())

    out = capsys.readouterr().out
    assert "❌ Unable to search users: API unreachable" in out
    assert "API unreachable" in str(e.value)
