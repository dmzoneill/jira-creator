#!/usr/bin/env python
"""
This module contains unit tests for a command-line interface (CLI) that interacts with JIRA issues.
It utilizes the `unittest` framework along with `MagicMock` for simulating JIRA responses.

Key Features:
- Shared base issue templates (`base_issue` and `base_issue_2`) for use in tests.
- A helper function `setup_cli_and_args` that configures the CLI context and issue data based on specified parameters.
- Several test functions (`test_list_print`, `test_list_reporter_print`, `test_list_with_filters`,
`test_list_with_blocked_filter`, and `test_list_with_unblocked_filter`) that verify the CLI's behavior
when listing issues with various filters and conditions.

Each test function captures the output of the CLI and asserts expected results based on the mocked JIRA issue data.
"""

from argparse import Namespace
from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ListIssuesError

rows = [
    {
        "key": "TEST-1",
        "issuetype": "story",
        "status": {"name": "To Do"},
        "assignee": {"displayName": "John Doe"},
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
        "sprint": "Sprint 2",
        "customfield_12310243": 5,
    },
]


@pytest.fixture
def mock_args():
    """Fixture for simulating command-line arguments."""
    return Namespace(
        project="TEST",
        component="COMPONENT",
        reporter=None,
        assignee=None,
        status=None,
        summary=None,
        blocked=None,
        unblocked=None,
        sort=None,
    )


def test_cli_list_issues_success(cli, mock_args, capsys):
    """Test case when issues are successfully listed."""

    cli.jira.list_issues = MagicMock()
    # Mock the JiraClient's list_issues method to return sample data
    cli.jira.list_issues.return_value = rows

    cli.jira.get_field_name = MagicMock()
    cli.jira.get_field_name.return_value = "story points"

    # Call the function with the mocked JiraClient and arguments
    result = cli.list_issues(mock_args)

    # Capture and check printed output
    captured = capsys.readouterr()
    assert "Test issue 1" in captured.out
    assert "Test issue 2" in captured.out

    # Check the returned issues
    assert len(result) == 2


def test_cli_list_issues_no_issues(cli, mock_args, capsys):
    """Test case when no issues are found."""

    # Mock the JiraClient's list_issues method to return an empty list
    cli.jira.list_issues.return_value = []

    # Call the function with the mocked JiraClient and arguments
    result = cli.list_issues(mock_args)

    # Capture and check printed output
    captured = capsys.readouterr()
    assert "No issues found." in captured.out

    # Check the returned issues
    assert result == []


def test_cli_list_issues_with_error(cli, mock_args):
    """Test case when there is an error while fetching issues."""

    # Mock the JiraClient's list_issues method to raise a ListIssuesError
    cli.jira.list_issues.side_effect = ListIssuesError("Failed to list issues")

    # Call the function and check that the exception is raised
    with pytest.raises(ListIssuesError):
        cli.list_issues(mock_args)


def test_cli_list_issues_with_filters(cli, mock_args, capsys):
    """Test case when filtering is applied on issues."""

    cli.jira.get_field_name = MagicMock()
    cli.jira.get_field_name.return_value = "story points"

    # Mock the JiraClient's list_issues method to return sample data
    cli.jira.list_issues.return_value = [rows[0]]

    # Modify the mock_args to include a summary filter
    mock_args.reporter = "john Swan"

    # Call the function with the mocked JiraClient and arguments
    result = cli.list_issues(mock_args)

    # Capture and check printed output
    captured = capsys.readouterr()
    assert "Test issue 1" in captured.out
    assert (
        "Test issue 2" not in captured.out
    )  # Issue 2 should be excluded by the filter

    # Check the returned issues
    assert len(result) == 1
