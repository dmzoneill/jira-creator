import io
from unittest.mock import MagicMock, patch

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import SearchError


def test_search(cli, mock_search_issues):
    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'In Progress'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify if the correct output is printed
        assert "AAP-mock_search_issues" in captured_output  # Issue key is printed
        assert "SaaS Sprint 2025-13" in captured_output  # Sprint name is printed
        assert "In Progress" in captured_output  # Status is printed
        assert "David O Neill" in captured_output  # Assignee name is printed


def test_search_no_issues(cli):
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
    # Mock search_issues to raise an exception
    cli.jira.search_issues = MagicMock(side_effect=SearchError("An error occurred"))

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'NonExistentStatus'"
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


def test_list_with_summary_filter(cli, capsys):
    # Mock list_issues to return a list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-test_list_with_summary_filter-1",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Dino"},
                "priority": {"name": "High"},
                EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                EnvFetcher.get("JIRA_SPRINT_FIELD"): ["name=Spring, state=ACTIVE"],
                "summary": "Fix bugs",
            },
        },
        {
            "key": "AAP-test_list_with_summary_filter-2",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "Low"},
                EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 3,
                EnvFetcher.get("JIRA_SPRINT_FIELD"): ["name=Summer, state=ACTIVE"],
                "summary": "Improve UX",
            },
        },
    ]

    # Mock the args with a summary filter
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "user": None,
            "assignee": None,
            "reporter": None,
            "status": None,
            "summary": "Fix",  # Only issues with "Fix" in the summary should be shown
            "blocked": None,
            "unblocked": None,
        },
    )

    # Run the list method with the summary filter
    cli.list_issues(args)

    captured = capsys.readouterr()

    assert "AAP-test_list_with_summary_filter-1" in captured.out
    assert "AAP-test_list_with_summary_filter-2" not in captured.out
