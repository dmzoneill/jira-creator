import io
from unittest.mock import MagicMock, patch

import pytest

from jira_creator.rh_jira import JiraCLI  # isort: skip


@pytest.fixture
def mock_cli():
    cli = JiraCLI()
    cli.jira = MagicMock()
    return cli


@pytest.fixture
def mock_search_issues(mock_cli):
    # Mock search_issues to return a list of issues
    mock_cli.jira.search_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-41844",
                "fields": {
                    "summary": "Run IQE tests in promotion pipelines",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "David O Neill"},
                    "priority": {"name": "Normal"},
                    "customfield_12310243": 5,
                    "customfield_12310940": [
                        """com.atlassian.greenhopper.service.sprint.Sprint@5063ab17[id=70766,
                        rapidViewId=18242,state=ACTIVE,name=SaaS Sprint 2025-13,"
                        startDate=2025-03-27T12:01:00.000Z,endDate=2025-04-03T12:01:00.000Z]"""
                    ],
                },
            }
        ]
    )


def test_search(mock_cli, mock_search_issues):
    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'In Progress'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        mock_cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify if the correct output is printed
        assert "AAP-41844" in captured_output  # Issue key is printed
        assert "SaaS Sprint 2025-13" in captured_output  # Sprint name is printed
        assert "In Progress" in captured_output  # Status is printed
        assert "David O Neill" in captured_output  # Assignee name is printed


def test_search_no_issues(mock_cli):
    # Mock search_issues to return an empty list of issues
    mock_cli.jira.search_issues = MagicMock(return_value=[])

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'NonExistentStatus'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        mock_cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify that no issues found message is printed
        assert "❌ No issues found for the given JQL." in captured_output


def test_search_with_exception(mock_cli):
    # Mock search_issues to raise an exception
    mock_cli.jira.search_issues = MagicMock(side_effect=Exception("An error occurred"))

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'NonExistentStatus'"
        assignee = None
        reporter = None

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        mock_cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify that the error message is printed
        assert "❌ Failed to search issues: An error occurred" in captured_output


def test_list_with_summary_filter(mock_cli, capsys):
    # Mock list_issues to return a list of issues
    mock_cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Dino"},
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12310940": ["name=Spring, state=ACTIVE"],
                "summary": "Fix bugs",
            },
        },
        {
            "key": "AAP-2",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "Low"},
                "customfield_12310243": 3,
                "customfield_12310940": ["name=Summer, state=ACTIVE"],
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
    mock_cli.list_issues(args)

    captured = capsys.readouterr()

    # Ensure only the "AAP-1" issue is printed (the one with "Fix" in the summary)
    assert "AAP-1" in captured.out
    assert (
        "AAP-2" not in captured.out
    )  # "AAP-2" should be skipped because its summary is "Improve UX"
