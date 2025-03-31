import io
from unittest.mock import MagicMock, patch

from jira_creator.rh_jira import JiraCLI  # Assuming JiraCLI is the class you're using


def test_search_exception_handling(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock the search_issues method to raise an exception
    cli.jira.search_issues.side_effect = Exception("Test Exception")

    # Create a mock Args object with a sample JQL query
    class Args:
        jql = "project = AAP AND status = 'In Progress'"

    # Run the search method, which should trigger the exception handling
    cli.search(Args)

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the exception message is printed correctly
    assert "❌ Failed to search issues: Test Exception" in captured.out


def test_search():
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock the search_issues method to return a list of issues
    cli.jira.search_issues = MagicMock(
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
                        "com.atlassian.greenhopper.service.sprint.Sprint@5063ab17[id=70766,rapidViewId=18242,state=ACTIVE,name=SaaS Sprint 2025-13,startDate=2025-03-27T12:01:00.000Z,endDate=2025-04-03T12:01:00.000Z]"
                    ],
                },
            }
        ]
    )

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'In Progress'"

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify if the correct output is printed
        assert "AAP-41844" in captured_output  # Issue key is printed
        assert "SaaS Sprint 2025-13" in captured_output  # Sprint name is printed
        assert "In Progress" in captured_output  # Status is printed
        assert "David O Neill" in captured_output  # Assignee name is printed


def test_search_no_issues():
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock the search_issues method to return an empty list of issues
    cli.jira.search_issues = MagicMock(return_value=[])

    # Prepare the args object to simulate CLI arguments
    class Args:
        jql = "project = AAP AND status = 'NonExistentStatus'"

    # Mock stdout to capture printed output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        cli.search(Args())

        # Capture the printed output
        captured_output = mock_stdout.getvalue()

        # Verify that no issues found message is printed
        assert "No issues found for the given JQL." in captured_output


def test_search_issues_none(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock the search_issues method to return None (to simulate the 'issues is None' scenario)
    cli.jira.search_issues.return_value = None

    # Create a mock Args object with a sample JQL query
    class Args:
        jql = "project = AAP AND status = 'In Progress'"

    # Run the search method, which should trigger the issues is None check
    cli.search(Args)

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the "No issues found" message is printed correctly
    assert "❌ No issues found. The search returned None." in captured.out


def test_list_with_summary_filter(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock list_issues to return a list of issues
    cli.jira.list_issues.return_value = [
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
            "status": None,
            "summary": "Fix",  # Only issues with "Fix" in the summary should be shown
            "blocked": None,
            "unblocked": None,
        },
    )

    # Run the list method with the summary filter
    cli.list_issues(args)

    captured = capsys.readouterr()

    # Ensure only the "AAP-1" issue is printed (the one with "Fix" in the summary)
    assert "AAP-1" in captured.out
    assert (
        "AAP-2" not in captured.out
    )  # "AAP-2" should be skipped because its summary is "Improve UX"


def test_list_with_blocked_filter(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock list_issues to return a list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Dino"},
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12310940": ["name=Spring, state=ACTIVE"],
                "customfield_12316543": {"value": "True"},
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
                "customfield_12316543": {"value": "False"},  # Not blocked
                "summary": "Improve UX",
            },
        },
    ]

    # Mock the args with the blocked filter set
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "user": None,
            "status": None,
            "summary": None,
            "blocked": True,  # Only blocked issues should be shown
            "unblocked": None,
        },
    )

    # Run the list method with the blocked filter
    cli.list_issues(args)

    captured = capsys.readouterr()

    # Ensure only the "AAP-1" issue is printed (the one with "True" in customfield_12316543)
    assert "AAP-1" in captured.out
    assert (
        "AAP-2" not in captured.out
    )  # "AAP-2" should be skipped because it's not blocked


def test_list_with_unblocked_filter(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock list_issues to return a list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Dino"},
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12310940": ["name=Spring, state=ACTIVE"],
                "customfield_12316543": {"value": "True"},  # Blocked
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
                "customfield_12316543": {"value": "False"},  # Not blocked
                "summary": "Improve UX",
            },
        },
    ]

    # Mock the args with the unblocked filter set
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "user": None,
            "status": None,
            "summary": None,
            "blocked": None,
            "unblocked": True,  # Only unblocked issues should be shown
        },
    )

    # Run the list method with the unblocked filter
    cli.list_issues(args)

    captured = capsys.readouterr()

    # Ensure only the "AAP-2" issue is printed (the one that is unblocked)
    assert "AAP-2" in captured.out
    assert "AAP-1" not in captured.out  # "AAP-1" should be skipped because it's blocked
