from unittest.mock import MagicMock, patch

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import LintAllError

import pytest  # isort: skip
from commands.cli_lint_all import print_status_table  # isort: skip


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
            "key": "AAP-test_print_status_table_with_wrapping-1",
            "summary": """This is a test summary that exceeds 120 characters
            to check the wrapping functionality of the print function. It should
            not split in the middle of a word.""",
            "progress": True,
        },
        {
            "key": "AAP-test_print_status_table_with_wrapping-2",
            "summary": "This summary is short.",
            "progress": False,
        },
        {
            "key": "AAP-test_print_status_table_with_wrapping-3",
            "summary": "This summary is short.",
            "progress": None,
        },
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
    assert "| ✅" in captured.out
    assert "| ❌" in captured.out


@pytest.mark.timeout(1)  # Timeout after 1 second for safety
def test_lint_all_all_pass(mock_save_cache, cli, capsys):
    cli.jira = MagicMock()

    # Mock the AI provider (if used in validation)
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.return_value = "OK"

    # Mock list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-test_lint_all_all_pass-1",
            "fields": {
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
                "reporter": None,
            },
        },
        {
            "key": "AAP-test_lint_all_all_pass-2",
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
                EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
                EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
                "status": {"name": "Refinement"},  # Status is "Refinement"
                "assignee": {"displayName": "Someone"},
                EnvFetcher.get(
                    "JIRA_EPIC_FIELD"
                ): "AAP-test_lint_all_all_pass-3",  # No Epic assigned for Story issues with Refinement status
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
        "commands.cli_lint_all.validate", return_value=[[], []]
    ):  # Correct patch for the validate function used in lint_all
        cli.lint_all(Args1())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Check assertions: we expect all issues to pass lint checks
        assert "✅ AAP-test_lint_all_all_pass-1 OK passed" in captured.out
        assert "✅ AAP-test_lint_all_all_pass-2 OK passed" in captured.out

    # Ensure the Args object has the required 'project' and other attributes
    class Args2:
        project = "TestProject"
        component = "analytics-hcc-service"
        reporter = "John"
        assignee = None

    # Patch validate where it's imported (in the lint_all module, not edit_issue)
    with patch(
        "commands.cli_lint_all.validate", return_value=[[], []]
    ):  # Correct patch for the validate function used in lint_all
        cli.lint_all(Args2())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Check assertions: we expect all issues to pass lint checks
        assert "✅ AAP-test_lint_all_all_pass-1 OK passed" in captured.out
        assert "✅ AAP-test_lint_all_all_pass-2 OK passed" in captured.out


def test_lint_all_no_issues(mock_save_cache, cli, capsys):
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


def test_lint_all_exception(mock_save_cache, cli, capsys):
    cli.jira = MagicMock()
    cli.jira.ai_provider = MagicMock()

    cli.jira.list_issues.side_effect = LintAllError("Simulated failure")

    with pytest.raises(LintAllError):
        cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "❌ Failed to lint issues: Simulated failure" in out


def test_lint_all_with_failures(mock_save_cache, cli, capsys):
    cli.jira = MagicMock()

    # Mock the AI provider (if used in validation)
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.return_value = "OK"

    # Mock list of issues
    # /* jscpd:ignore-start */
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-test_lint_all_with_failures-1",
            "fields": {
                "key": "AAP-test_lint_all_with_failures-1",
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
                "reporter": None,
            },
        },
        {
            "key": "AAP-test_lint_all_with_failures-2",
            "fields": {
                "key": "AAP-test_lint_all_with_failures-2",
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
                EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
                EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
                "status": {"name": "Refinement"},  # Status is "Refinement"
                "assignee": {"displayName": "Someone"},
                EnvFetcher.get(
                    "JIRA_EPIC_FIELD"
                ): None,  # No Epic assigned for Story issues with Refinement status
                "reporter": None,
            }
        }

    # /* jscpd:ignore-end */

    cli.jira._request = mock_request

    # Patch validate to return problems
    with patch(
        "commands.cli_lint_all.validate",
        return_value=[["❌ Issue has no assigned Epic"], []],
    ):
        cli.lint_all(Args())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Assert that the lint check failure output is captured
        assert (
            "❌ AAP-test_lint_all_with_failures-1 OK failed lint checks" in captured.out
        )
        assert (
            "❌ AAP-test_lint_all_with_failures-2 OK failed lint checks" in captured.out
        )
        assert "⚠️ Issues with lint problems:" in captured.out
        assert "🔍 AAP-test_lint_all_with_failures-1 - OK" in captured.out
        assert " - ❌ Issue has no assigned Epic" in captured.out
