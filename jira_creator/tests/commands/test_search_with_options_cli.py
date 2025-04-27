#!/usr/bin/env python
"""
Unit tests for the CLI search and list functionality of a JIRA integration.

This module contains a series of tests that validate the behavior of the CLI's search and list issue functionalities.
It uses the pytest framework along with unittest.mock to simulate JIRA responses and capture output for verification.

Tests include:
- Searching for issues based on JQL queries and verifying the correct output is printed.
- Handling cases where no issues are found and ensuring the appropriate message is displayed.
- Managing exceptions raised during search operations and confirming error messages are printed.
- Filtering listed issues by summary to ensure only relevant results are shown.

Dependencies:
- pytest
- unittest.mock
- core.env_fetcher (for environment variable fetching)
- exceptions.exceptions (for handling specific errors)
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import SearchError

# /* jscpd:ignore-start */
rows = [
    {
        "key": "AAP-mock_search_issues",
        "issuetype": "story",
        "status": {"name": "To Do"},
        "assignee": {"displayName": "David O Neill"},
        "reporter": {"displayName": "john Swan"},
        "priority": {"name": "High"},
        "summary": "Test issue 1",
        "sprint": "Sprint 1",
        "customfield_12310243": 5,
    },
    {
        "key": "TEST-2",
        "issuetype": "story",
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Jane Smith"},
        "reporter": {"displayName": "Mike Swan"},
        "priority": {"name": "Medium"},
        "summary": "Test issue 2",
        "sprint": "SaaS Sprint 2025-13",
        "customfield_12310243": 5,
    },
]
# /* jscpd:ignore-end */


def test_search(cli, mock_search_issues):
    """
    Simulate a search functionality for issues using a mock search.

    Arguments:
    - cli (object): An object representing the command-line interface.
    - mock_search_issues (object): A mock object used to simulate the search for issues.

    Side Effects:
    - Prepares the 'Args' object to simulate CLI arguments for the search.

    Note: This function does not have a return value.
    """

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'In Progress'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        cli.jira.get_field_name = MagicMock()
        cli.jira.get_field_name.return_value = "story points"
        cli.jira.search_issues = MagicMock()
        cli.jira.search_issues.return_value = rows

        cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify if the correct output is printed
        assert "AAP-mock_search_issues" in captured_output  # Issue key is printed
        assert "SaaS Sprint 2025-13" in captured_output  # Sprint name is printed
        assert "In Progress" in captured_output  # Status is printed
        assert "David O Neill" in captured_output  # Assignee name is printed


def test_search_no_issues(cli):
    """
    Simulate a test scenario where the search_issues function returns an empty list of issues.

    Arguments:
    - cli: An object representing the command-line interface.

    Side Effects:
    - Modifies the search_issues function of the Jira client to return an empty list of issues.
    """

    # Mock search_issues to return an empty list of issues
    cli.jira.search_issues = MagicMock(return_value=[])

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'NonExistentStatus'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify that no issues found message is printed
        assert "❌ No issues found for the given JQL." in captured_output


def test_search_with_exception(cli):
    """
    Mock the search_issues method of the provided cli object to raise a SearchError exception with the message "An
    error occurred".

    Arguments:
    - cli: An object representing the command-line interface (CLI) that contains a method for searching issues.

    Exceptions:
    - SearchError: Raised when the search_issues method of the cli object encounters an error.

    Side Effects:
    - Modifies the behavior of the search_issues method in the cli object to raise a SearchError exception with the
    specified message.
    - Captures and verifies the printed output when the exception is raised during the search operation.
    """

    # Mock search_issues to raise an exception
    cli.jira.search_issues = MagicMock(side_effect=SearchError("An error occurred"))

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'NonExistentStatus'"
        query = "project = AAP AND status = 'NonExistentStatus'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        with pytest.raises(SearchError):
            cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify that the error message is printed
        assert "❌ Failed to search issues: An error occurred" in captured_output
