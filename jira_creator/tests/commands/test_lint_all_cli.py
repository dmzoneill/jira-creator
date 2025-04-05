from unittest.mock import MagicMock, patch

import pytest
from jira_creator.commands.cli_lint_all import print_status_table


# Ensure the Args object has the required 'project' and other attributes
class Args:
    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"
    reporter = None
    assignee = None


class ArgsReporter:
    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"
    reporter = "test"
    assignee = None


class ArgsAssignee:
    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"
    reporter = None
    assignee = "test"


def test_print_status_table_with_wrapping(capsys):
    # Prepare the mock data
    failure_statuses = [
        {
            "key": "AAP-1",
            "summary": """This is a test summary that exceeds 120 characters
            to check the wrapping functionality of the print function. It should
            not split in the middle of a word.""",
            "progress": True,
        },
        {"key": "AAP-2", "summary": "This summary is short.", "progress": False},
        {"key": "AAP-3", "summary": "This summary is short.", "progress": None},
    ]

    # Call the function with the mock data
    print_status_table(failure_statuses)

    # Capture the output
    captured = capsys.readouterr()
    # Check if the correct symbols for progress are shown
    assert "✅" in captured.out  # for the row with progress = True
    assert "❌" in captured.out  # for the row with progress = False

    # Ensure the correct columns exist in the output (check that the headers contain the expected keys)
    headers = ["key", "summary", "progress"]
    for header in headers:
        assert f"| {header} |" in captured.out  # Check that each header appears

    # Check that the rows have the correct values
    assert "| ✅" in captured.out  # for AAP-1
    assert "| ❌" in captured.out  # for AAP-2


@pytest.mark.timeout(1)  # Timeout after 1 second for safety
def test_lint_all_all_pass(cli, capsys):
    cli.jira = MagicMock()

    # Mock the AI provider (if used in validation)
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.return_value = "OK"

    # Mock list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
                "reporter": None,
            },
        },
        {
            "key": "AAP-2",
            "fields": {
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
                "reporter": None,
            },
        },
    ]

    # Mock the request function to return the issue details
    def mock_request(method, path, **kwargs):
        return {
            "fields": {
                "summary": "OK",
                "description": "OK",
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12316543": {"value": "False"},
                "customfield_12316544": "",
                "status": {"name": "Refinement"},  # Status is "Refinement"
                "assignee": {"displayName": "Someone"},
                "customfield_12311140": "AAP-7654",  # No Epic assigned for Story issues with Refinement status
                "reporter": None,
            }
        }

    cli.jira._request = mock_request

    # Ensure the Args object has the required 'project' and other attributes
    class Args1:
        project = "TestProject"
        component = "analytics-hcc-service"
        reporter = None
        assignee = None

    # Patch validate where it's imported (in the lint_all module, not edit_issue)
    with patch(
        "jira_creator.commands.cli_lint_all.validate", return_value=[[], []]
    ):  # Correct patch for the validate function used in lint_all
        cli.lint_all(Args1())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Check assertions: we expect all issues to pass lint checks
        assert "✅ AAP-1 OK passed" in captured.out
        assert "✅ AAP-2 OK passed" in captured.out

    # Ensure the Args object has the required 'project' and other attributes
    class Args2:
        project = "TestProject"
        component = "analytics-hcc-service"
        reporter = "John"
        assignee = None

    # Patch validate where it's imported (in the lint_all module, not edit_issue)
    with patch(
        "jira_creator.commands.cli_lint_all.validate", return_value=[[], []]
    ):  # Correct patch for the validate function used in lint_all
        cli.lint_all(Args2())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Check assertions: we expect all issues to pass lint checks
        assert "✅ AAP-1 OK passed" in captured.out
        assert "✅ AAP-2 OK passed" in captured.out


def test_lint_all_no_issues(cli, capsys):
    cli.jira = MagicMock()
    cli.jira.ai_provider = MagicMock()

    cli.jira.list_issues.return_value = []

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "✅ No issues assigned to you." in out

    cli.lint_all(ArgsReporter())
    out = capsys.readouterr().out

    assert "✅ No issues assigned to you." in out

    cli.lint_all(ArgsAssignee())
    out = capsys.readouterr().out

    assert "✅ No issues assigned to you." in out


def test_lint_all_exception(cli, capsys):
    cli.jira = MagicMock()
    cli.jira.ai_provider = MagicMock()

    cli.jira.list_issues.side_effect = Exception("Simulated failure")

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "❌ Failed to lint issues: Simulated failure" in out


def test_lint_all_with_failures(cli, capsys):
    cli.jira = MagicMock()

    # Mock the AI provider (if used in validation)
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.return_value = "OK"

    # Mock list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "key": "AAP-1",
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
                "reporter": None,
            },
        },
        {
            "key": "AAP-2",
            "fields": {
                "key": "AAP-2",
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
                "reporter": None,
            },
        },
    ]

    # Mock the request function to return the issue details
    def mock_request(method, path, **kwargs):
        return {
            "fields": {
                "summary": "OK",
                "description": "OK",
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12316543": {"value": "False"},
                "customfield_12316544": "",
                "status": {"name": "Refinement"},  # Status is "Refinement"
                "assignee": {"displayName": "Someone"},
                "customfield_12311140": None,  # No Epic assigned for Story issues with Refinement status
                "reporter": None,
            }
        }

    cli.jira._request = mock_request

    # Patch validate to return problems
    with patch(
        "jira_creator.commands.cli_lint_all.validate",
        return_value=[["❌ Issue has no assigned Epic"], []],
    ):
        cli.lint_all(Args())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Assert that the lint check failure output is captured
        assert "❌ AAP-1 OK failed lint checks" in captured.out
        assert "❌ AAP-2 OK failed lint checks" in captured.out
        assert "⚠️ Issues with lint problems:" in captured.out
        assert "🔍 AAP-1 - OK" in captured.out
        assert " - ❌ Issue has no assigned Epic" in captured.out
