from argparse import Namespace
from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_acceptance_criteria(cli, capsys):
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
    # Mock the JiraClient used within JiraCLI
    cli.jira = MagicMock()

    issue_key = "AAP-test_set_acceptance_criteria_exception"
    acceptance_criteria = "Acceptance criteria description"

    # Simulate the exception being raised by the set_acceptance_criteria method
    cli.jira.set_acceptance_criteria.side_effect = Exception("Some error occurred")

    # Simulate args being passed from the parser
    args = Namespace(issue_key=issue_key, acceptance_criteria=acceptance_criteria)

    # Call the set_acceptance_criteria method of JiraCLI, which should internally call the JiraClient
    cli.set_acceptance_criteria(args)

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to set acceptance criteria: Some error occurred" in out
