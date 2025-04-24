#!/usr/bin/env python
"""
This module contains unit tests for the quarterly connection report functionality in the command-line interface (CLI).

The tests included in this module cover various scenarios for generating quarterly connection reports:
- `test_quarterly_connection_report_success`: Verifies successful execution of the quarterly connection report.
- `test_quarterly_connection_report_no_issues`: Checks the behavior when no issues are found for the quarterly
connection report.
- `test_quarterly_connection_report_error`: Tests the handling of `QuarterlyConnectionError` during the report
generation process.

The tests utilize mocking techniques, specifically `MagicMock` and `patch`, to isolate and control the behavior of
methods and classes involved in the report generation.
"""

from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import QuarterlyConnectionError


def test_quarterly_connection_report_sucess(cli):
    """
    Generate a quarterly connection report successfully.

    Arguments:
    - cli: An instance of a command-line interface (CLI) used to interact with the system.

    This function mocks the _register_subcommands and _dispatch_command methods to generate a quarterly connection
    report successfully.
    """

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
    """
    Generates a quarterly connection report without any issues.

    Arguments:
    - cli: An object representing the command-line interface.

    Side Effects:
    - Mocks the _register_subcommands and _dispatch_command methods.
    """

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
    """
    Generates a quarterly connection report error for a given CLI.

    Arguments:
    - cli (object): An object representing the CLI for which the report error will be generated.

    Side Effects:
    - Mocks the _register_subcommands and _dispatch_command methods internally.
    """

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
