from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import GetUserError


def test_cli_view_user_prints_user_fields(cli, capsys):
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
    assert "accountId : abc123" in out
    assert "displayName : David O'Neill" in out
    assert "emailAddress : daoneill@redhat.com" in out


def test_cli_view_user_raises_and_prints_error(cli, capsys):
    cli.jira.get_user = MagicMock()
    cli.jira.get_user.side_effect = GetUserError("User not found")

    class Args:
        account_id = "notreal"

    with pytest.raises(GetUserError) as e:
        cli.view_user(Args())

    out = capsys.readouterr().out
    assert "❌ Unable to retrieve user: User not found" in out
    assert "User not found" in str(e.value)
