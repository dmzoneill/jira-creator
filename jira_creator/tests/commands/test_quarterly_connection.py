from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import QuarterlyConnectionError


def test_quarterly_connection_report_sucess(cli):
    # Mocking the _register_subcommands and _dispatch_command methods
    class Args:
        issue_key = "AAP-test_edit_with_ai"
        no_ai = False
        lint = False

    mock_fields = [{"key": "", "fields": {"summary": "CVE"}}, {"key": "", "fields": {}}]

    with patch("commands.cli_quarterly_connection.time.sleep"):
        cli.jira.search_issues = MagicMock(return_value=mock_fields)
        cli.jira.get_description = MagicMock()
        cli.ai_provider = MagicMock()
        cli.quarterly_connection(Args())


def test_quarterly_connection_report_no_issues(cli):
    # Mocking the _register_subcommands and _dispatch_command methods
    class Args:
        issue_key = "AAP-test_edit_with_ai"
        no_ai = False
        lint = False

    mock_fields = []

    with patch("commands.cli_quarterly_connection.time.sleep"):
        cli.jira.search_issues = MagicMock(return_value=mock_fields)
        cli.jira.get_description = MagicMock()
        cli.ai_provider = MagicMock()
        cli.quarterly_connection(Args())


def test_quarterly_connection_report_error(cli):
    # Mocking the _register_subcommands and _dispatch_command methods
    class Args:
        issue_key = "AAP-test_edit_with_ai"
        no_ai = False
        lint = False

    with patch("commands.cli_quarterly_connection.time.sleep"):
        cli.jira.search_issues = MagicMock(side_effect=QuarterlyConnectionError)
        cli.jira.get_description = MagicMock()
        cli.ai_provider = MagicMock()
        with pytest.raises(QuarterlyConnectionError):
            cli.quarterly_connection(Args())
