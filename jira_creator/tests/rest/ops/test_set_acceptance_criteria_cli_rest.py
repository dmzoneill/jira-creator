"""
This file contains unit tests for the set_acceptance_criteria method in a JiraCLI class.
It includes tests for both the normal behavior and an exception scenario.
The tests mock the JiraClient and simulate GET and PUT responses.
The first test validates the successful setting of acceptance criteria, while the second test checks the handling of a
SetAcceptanceCriteriaError exception.
The output of the method calls is captured and assertions are made on the printed messages.
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
    cli.jira._request.side_effect = [
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
