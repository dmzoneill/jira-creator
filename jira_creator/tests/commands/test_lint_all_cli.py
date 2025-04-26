#!/usr/bin/env python
"""
Unit tests for the linting functionality of a CLI application that interacts with JIRA issues.

This module includes various test cases to validate the behavior of the `lint_all` command and the output formatting of
the `print_status_table` function. It utilizes the `pytest` framework and employs mocking to simulate JIRA interactions
and responses.

Key features tested include:
- Correct output formatting for issues with varying progress statuses.
- Handling of scenarios with no issues assigned, ensuring appropriate messages are displayed.
- Validation of lint checks, including cases where issues pass and fail linting criteria.
- Exception handling for simulated errors during JIRA issue retrieval.

Classes:
- Args: A simple class to simulate command-line arguments for linting.
- ArgsReporter: A variant of Args with a specified reporter.
- ArgsAssignee: A variant of Args with a specified assignee.

Functions:
- test_print_status_table_with_wrapping: Tests the output of the print_status_table function with wrapped text.
- test_lint_all_all_pass: Tests the behavior when all issues pass the lint checks.
- test_lint_all_no_issues: Tests the output when no issues are found.
- test_lint_all_exception: Tests the behavior when an exception occurs during linting.
- test_lint_all_with_failures: Tests the output when some issues fail lint checks.
"""

from unittest.mock import MagicMock, patch

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import LintAllError

import pytest  # isort: skip
from commands.cli_lint_all import print_status_table  # isort: skip


# Ensure the Args object has the required 'project' and other attributes
class Args:
    """
    This class represents a set of arguments used for a specific project.

    Attributes:
    project (str): The name of the project. Default value is "TestProject".
    component (str): The component related to the project, default value is "analytics-hcc-service".
    reporter: The user responsible for reporting on the project, default value is None.
    assignee: The user assigned to work on the project, default value is None.
    """

    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"
    reporter = None
    assignee = None


class ArgsReporter:
    """
    This class represents an ArgsReporter used for reporting project-related information.

    Attributes:
    project (str): The name of the project being reported on (e.g., "TestProject").
    component (str): The specific component within the project (e.g., "analytics-hcc-service").
    reporter (str): The name of the person reporting on the project (e.g., "test").
    assignee (NoneType): The person assigned to work on the project, can be None if not assigned yet.
    """

    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"
    reporter = "test"
    assignee = None


class ArgsAssignee:
    """
    This class represents an assignee for a specific project.

    Attributes:
    project (str): The name of the project the assignee is associated with.
    component (str): The specific component within the project.
    reporter: The person responsible for reporting on the project.
    assignee (str): The name of the assignee for the project.
    """

    project = "TestProject"  # Add the required 'project' attribute
    component = "analytics-hcc-service"
    reporter = None
    assignee = "test"


def test_print_status_table_with_wrapping(capsys):
    """
    Prints a status table with wrapping functionality for the given data.

    Arguments:
    - capsys: A pytest fixture for capturing stdout and stderr output.

    Side Effects:
    - Prints a formatted status table with wrapping functionality for the provided data.
    """

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
    """
    Set up a mock cache, CLI, and capture system stdout/stderr for testing purposes.
    Assign a MagicMock object to the 'jira' attribute of the CLI object.
    Parameters:
    - mock_save_cache: Mock object for saving cache.
    - cli: CLI object for testing.
    - capsys: Capturing system standard output and error streams.
    """

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
        """
        Simulate a mock request and return a dictionary with predefined fields.

        Arguments:
        - method (str): The HTTP method used in the request.
        - path (str): The path or endpoint of the request.
        - **kwargs: Additional keyword arguments that are not used in this function.

        Return:
        - dict: A dictionary containing predefined fields such as summary, description, priority, status, assignee, etc.

        Side Effects:
        - This function does not have any side effects as it only returns a predefined dictionary.
        """

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

    cli.jira.request = mock_request

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
    """
    Simulate linting all files with no issues.

    Arguments:
    - mock_save_cache: A MagicMock object for saving cache.
    - cli: An object representing the CLI.
    - capsys: A fixture to capture stdout and stderr outputs.

    Side Effects:
    - Sets up a mock Jira object and its AI provider in the CLI object.
    """

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
    """
    Lint all exceptions that occur during the test.

    Arguments:
    - mock_save_cache: Mock object for saving cache.
    - cli: Command-line interface object.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Side Effects:
    - Modifies the 'jira' attribute of the 'cli' object by assigning a MagicMock object to it.
    - Modifies the 'ai_provider' attribute of the 'cli.jira' object by assigning a MagicMock object to it.
    """

    cli.jira = MagicMock()
    cli.jira.ai_provider = MagicMock()

    cli.jira.list_issues.side_effect = LintAllError("Simulated failure")

    with pytest.raises(LintAllError):
        cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "❌ Failed to lint issues: Simulated failure" in out


def test_lint_all_with_failures(mock_save_cache, cli, capsys):
    """
    Run linting on all files and handle failures gracefully.

    Arguments:
    - mock_save_cache: MagicMock object for saving cache.
    - cli: Command Line Interface object.
    - capsys: pytest fixture for capturing stdout and stderr.

    Side Effects:
    - Sets the 'jira' attribute of the 'cli' object to a MagicMock object.
    - Sets the 'ai_provider' attribute of the 'cli' object to a MagicMock object with a mocked 'improve_text' method.
    - Modifies the return value of 'cli.jira.list_issues' to a list of dictionaries representing mocked issues.
    """

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
        """
        Simulates a mock HTTP request with the specified method, path, and additional keyword arguments, and returns a
        dictionary containing simulated response fields.

        Arguments:
        - method (str): The HTTP method used in the request (e.g., GET, POST).
        - path (str): The path or endpoint of the request.
        - **kwargs: Additional keyword arguments that can be used to customize the mock request.

        Return:
        dict: A dictionary containing simulated response fields such as summary, description, priority, status,
        assignee, reporter, and custom fields fetched using EnvFetcher.

        Side Effects:
        - This function does not have any side effects as it only generates a mock response dictionary.
        """

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

    cli.jira.request = mock_request

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
