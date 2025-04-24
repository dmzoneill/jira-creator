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

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher

# Shared dictionary for issue data
base_issue = {
    "key": "AAP",
    "fields": {
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Dino"},
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        EnvFetcher.get("JIRA_BLOCKED_FIELD"): True,
        EnvFetcher.get("JIRA_SPRINT_FIELD"): ["name=Spring, state=ACTIVE"],
        "summary": "Fix bugs",
    },
}

base_issue_2 = {
    "key": "AAP",
    "fields": {
        "status": {"name": "Done"},
        "assignee": {"displayName": "Alice"},
        "priority": {"name": "Low"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 3,
        EnvFetcher.get("JIRA_BLOCKED_FIELD"): False,
        EnvFetcher.get("JIRA_SPRINT_FIELD"): ["name=Summer, state=ACTIVE"],
        "summary": "Improve UX",
    },
}

# Helper function to return common setup with different params


def setup_cli_and_args(
    cli,
    blocked=None,
    unblocked=None,
    reporter=None,
    status=None,
    summary=None,
    func=None,
):
    """
    Setup the Jira mock for the CLI.

    Arguments:
    - cli (object): The CLI object to which the Jira mock will be assigned.
    - blocked (list): List of blocked items (default is None).
    - unblocked (list): List of unblocked items (default is None).
    - reporter (str): Name of the reporter (default is None).
    - status (str): Status of the items (default is None).
    - summary (str): Summary of the items (default is None).
    - func (function): Function to be executed (default is None).

    Side Effects:
    - Modifies the 'jira' attribute of the 'cli' object by assigning it a MagicMock object.
    """

    # Setup the Jira mock
    cli.jira = MagicMock()

    b1 = base_issue.copy()
    b2 = base_issue_2.copy()
    b1["key"] = b1["key"] + "-" + func + "-1"
    b2["key"] = b2["key"] + "-" + func + "-2"

    if blocked:
        print(b1)
        b1["fields"]["status"]["name"] = "In Progres"
        b2["fields"]["status"]["name"] = "In Progres"

    # Setup the issues (base_issue and base_issue_2 can be modified in each test)
    issues = [b1, b2]

    # Modify issues if required
    if summary:
        issues[0]["fields"]["summary"] = summary
    if reporter:
        issues[1]["fields"]["reporter"] = reporter
    if status:
        issues[0]["fields"]["status"]["name"] = status

    # Setup args with the passed filters
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "assignee": None,
            "status": status,
            "summary": summary,
            "blocked": blocked,
            "unblocked": unblocked,
            "reporter": reporter,
        },
    )

    return args, issues


def test_list_print(cli, capsys):
    """
    Print a list of issues using the provided CLI.

    Arguments:
    - cli (object): The CLI object used to interact with the command-line interface.
    - capsys (object): The capsys object used to capture stdout and stderr outputs.

    Side Effects:
    - Modifies the behavior of the provided CLI object by listing the retrieved issues.
    """

    args, issues = setup_cli_and_args(cli, func="test_list_print")
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_print" in captured.out


def test_list_reporter_print(cli, capsys):
    """
    Print a list of reported issues.

    Arguments:
    - cli: An object representing the command line interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr outputs.

    Side Effects:
    - Modifies the summary for a test case.
    - Sets up command line arguments.
    - Retrieves a list of reported issues using the provided CLI object.
    """

    # Modify summary for this test case
    summary = "Fix bugs" * 20  # Update summary for this test case
    args, issues = setup_cli_and_args(
        cli, summary=summary, reporter="John", func="test_list_reporter_print"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_reporter_print" in captured.out


def test_list_with_filters(cli, capsys):
    """
    Execute a test for listing Jira issues with filters.

    Arguments:
    - cli: An instance of the CLI (Command Line Interface) used for interacting with Jira.
    - capsys: Pytest fixture for capturing stdout and stderr output during testing.

    Side Effects:
    - Modifies the CLI configuration with specified status and function.
    - Sets up the return value of listing Jira issues to the provided issues.
    - Calls the list_issues method of the CLI instance.

    Note: This function is primarily designed for testing purposes and does not have a return value.
    """

    args, issues = setup_cli_and_args(
        cli, status="In Progress", func="test_list_with_filters"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_with_filters-1" in captured.out
    assert "AAP-test_list_with_filters-2" not in captured.out


def test_list_with_blocked_filter(cli, capsys):
    """
    Filter and list issues based on a blocked filter.

    Arguments:
    - cli: An object representing the command-line interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Side Effects:
    - Modifies the behavior of the command-line interface by setting up arguments with a blocked filter.
    - Calls the setup_cli_and_args function to configure the CLI arguments.
    - Sets the return value of cli.jira.list_issues to the provided issues.
    - Invokes the list_issues method of the CLI.
    """

    args, issues = setup_cli_and_args(
        cli, blocked=True, func="test_list_with_blocked_filter"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_with_blocked_filter-1" in captured.out
    assert "AAP-test_list_with_blocked_filter-2" in captured.out


def test_list_with_unblocked_filter(cli, capsys):
    """
    Filter and list Jira issues based on the unblocked status.

    Arguments:
    - cli: An object representing the command-line interface for interacting with Jira.
    - capsys: A pytest fixture for capturing stdout and stderr output.

    Side Effects:
    - Modifies the behavior of the Jira CLI by setting up the appropriate arguments and filters.
    - Calls the 'list_issues' method of the Jira CLI to retrieve and display a list of filtered issues.

    Note: This function assumes the existence of 'setup_cli_and_args' and 'list_issues' methods within the 'cli' object.
    """

    args, issues = setup_cli_and_args(
        cli, unblocked=True, func="test_list_with_unblocked_filter"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_with_unblocked_filter-1" in captured.out
    assert "AAP-test_list_with_unblocked_filter-2" not in captured.out
