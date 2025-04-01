from unittest.mock import MagicMock, patch

import pytest

from jira_creator.rh_jira import JiraCLI


# Ensure the Args object has the required 'project' and other attributes
class Args:
    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"


@pytest.mark.timeout(1)  # Timeout after 1 second for safety
def test_lint_all_all_pass(capsys):
    cli = JiraCLI()
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
            },
        },
        {
            "key": "AAP-2",
            "fields": {
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
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
            }
        }

    cli.jira._request = mock_request

    # Ensure the Args object has the required 'project' and other attributes
    class Args:
        project = "TestProject"
        component = "analytics-hcc-service"

    # Patch validate where it's imported (in the lint_all module, not edit_issue)
    with patch(
        "jira_creator.rh_jira.lint_all.validate", return_value=[]
    ):  # Correct patch for the validate function used in lint_all
        cli.lint_all(Args())

        # Capture and print output
        captured = capsys.readouterr()
        print(f"Captured Output:\n{captured.out}")

        # Check assertions: we expect all issues to pass lint checks
        assert "✅ AAP-1 OK passed" in captured.out
        assert "✅ AAP-2 OK passed" in captured.out


def test_lint_all_no_issues(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.jira.ai_provider = MagicMock()

    cli.jira.list_issues.return_value = []

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "✅ No issues assigned to you." in out


def test_lint_all_exception(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.jira.ai_provider = MagicMock()

    cli.jira.list_issues.side_effect = Exception("Simulated failure")

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "❌ Failed to lint issues: Simulated failure" in out


def test_lint_all_with_failures(capsys):
    cli = JiraCLI()
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
            },
        },
        {
            "key": "AAP-2",
            "fields": {
                "issuetype": {"name": "Story"},
                "status": {"name": "Refinement"},
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
            }
        }

    cli.jira._request = mock_request

    # Patch validate to return problems
    with patch(
        "jira_creator.rh_jira.lint_all.validate",
        return_value=["❌ Issue has no assigned Epic"],
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
