#!/usr/bin/env python
"""
Unit tests for the `set_acceptance_criteria` method of the `JiraCLI` class.

This module contains unit tests that validate the functionality of the `set_acceptance_criteria` method
in the `JiraCLI` class. The tests ensure correct handling of both successful scenarios and exceptions,
utilizing mocking to simulate interactions with the `JiraClient`.

Test Functions:
- `test_set_acceptance_criteria`: Tests the successful setting of acceptance criteria and checks the
expected console output.
- `test_set_acceptance_criteria_exception`: Tests the error handling when a `SetAcceptanceCriteriaError`
is raised, verifying the output message.

Dependencies:
- `pytest`: Required for running the tests and capturing output.
- `unittest.mock`: Used for creating mock objects of the `JiraClient` to avoid real API calls.
- Custom exceptions and environment fetching utilities from the core application.

Usage:
Run the tests using pytest to ensure the `set_acceptance_criteria` method behaves correctly in both
normal and error conditions.
"""

from argparse import Namespace
from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import SetAcceptanceCriteriaError


def test_set_acceptance_criteria(cli, capsys):
    """
    Sets up the acceptance criteria for testing a JiraCLI command.

    Arguments:
    - cli (JiraCLI): An instance of the JiraCLI class.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Side Effects:
    - Modifies the 'jira' attribute of the provided JiraCLI instance by assigning a MagicMock object to it.
    """

    # Mock the JiraClient used within JiraCLI
    cli.jira = MagicMock()

    issue_key = "AAP-test_set_acceptance_criteria"
    acceptance_criteria = "Acceptance criteria description"

    # Simulate the GET and PUT responses for the JiraClient's _request method
    cli.jira.request.side_effect = [
        {
            "fields": {
                EnvFetcher.get(
                    "JIRA_ACCEPTANCE_CRITERIA_FIELD"
                ): "Acceptance criteria description"
            }
        },  # GET response with 'fields'
        {},  # PUT response (successful)
    ]

    # Simulate args being passed from the parser
    args = Namespace(issue_key=issue_key, acceptance_criteria=acceptance_criteria)

    # Call the set_acceptance_criteria method of JiraCLI, which should internally call the JiraClient
    cli.set_acceptance_criteria(args)

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct output was printed
    assert "✅ Acceptance criteria set to 'Acceptance criteria description'" in out


def test_set_acceptance_criteria_exception(cli, capsys):
    """
    Set acceptance criteria for a test case and handle exceptions.

    Arguments:
    - cli (JiraCLI): An instance of JiraCLI class.
    - capsys: pytest fixture to capture stdout and stderr.

    Side Effects:
    - Modifies the JiraClient object within the JiraCLI instance.
    """

    # Mock the JiraClient used within JiraCLI
    cli.jira = MagicMock()

    issue_key = "AAP-test_set_acceptance_criteria_exception"
    acceptance_criteria = "Acceptance criteria description"

    # Simulate the exception being raised by the set_acceptance_criteria method
    cli.jira.set_acceptance_criteria.side_effect = SetAcceptanceCriteriaError(
        "Some error occurred"
    )

    # Simulate args being passed from the parser
    args = Namespace(issue_key=issue_key, acceptance_criteria=acceptance_criteria)

    with pytest.raises(SetAcceptanceCriteriaError):
        # Call the set_acceptance_criteria method of JiraCLI, which should internally call the JiraClient
        cli.set_acceptance_criteria(args)

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to set acceptance criteria: Some error occurred" in out
