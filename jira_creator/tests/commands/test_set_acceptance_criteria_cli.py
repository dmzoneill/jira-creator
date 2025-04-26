from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetAcceptanceCriteriaError


# /* jscpd:ignore-start */
def test_cli_set_acceptance_criteria_success(cli, capsys):
    """
    Tests the successful case where acceptance criteria are set for a Jira issue.
    """

    # Mock the set_acceptance_criteria method
    cli.jira.set_acceptance_criteria = MagicMock(return_value=None)

    # Mock the improve_text method
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-12345"
        acceptance_criteria = "Acceptance criteria is clear"

    # Call the cli_set_acceptance_criteria method
    result = cli.set_acceptance_criteria(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the result is True
    assert result is True

    # Check that the correct success message is printed
    assert "✅ Acceptance criteria set to 'Acceptance criteria is clear'" in out


def test_cli_set_acceptance_criteria_invalid_issue_key(cli):
    """
    Tests the case where the issue key is invalid.
    """

    class Args:
        issue_key = ""  # Invalid issue key
        acceptance_criteria = "Some criteria"

    # Expecting a ValueError due to invalid issue key
    with pytest.raises(ValueError):
        cli.set_acceptance_criteria(Args())


def test_cli_set_acceptance_criteria_invalid_acceptance_criteria(cli):
    """
    Tests the case where the acceptance criteria is invalid.
    """

    class Args:
        issue_key = "AAP-12345"
        acceptance_criteria = ""  # Invalid acceptance criteria

    # Expecting a ValueError due to invalid acceptance criteria
    with pytest.raises(ValueError):
        cli.set_acceptance_criteria(Args())


def test_cli_set_acceptance_criteria_set_error(cli, capsys):
    """
    Tests the error handling when the SetAcceptanceCriteriaError is raised.
    """
    # Mock the set_acceptance_criteria method to raise an error
    cli.jira.set_acceptance_criteria = MagicMock(
        side_effect=SetAcceptanceCriteriaError("Failed to set criteria")
    )

    # Mock the improve_text method
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-12345"
        acceptance_criteria = "Acceptance criteria"

    # Call the cli_set_acceptance_criteria method and handle the exception
    with pytest.raises(SetAcceptanceCriteriaError):
        cli.set_acceptance_criteria(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the correct error message is printed
    assert "❌ Failed to set acceptance criteria" in out


def test_cli_set_acceptance_criteria_unexpected_error(cli, capsys):
    """
    Tests the case where an unexpected error occurs while setting the acceptance criteria.
    """
    # Mock the set_acceptance_criteria method to raise an unexpected error
    cli.jira.set_acceptance_criteria = MagicMock(
        side_effect=Exception("Unexpected error")
    )

    # Mock the improve_text method
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-12345"
        acceptance_criteria = "Acceptance criteria"

    # Call the cli_set_acceptance_criteria method and handle the exception
    with pytest.raises(SetAcceptanceCriteriaError):
        cli.set_acceptance_criteria(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the correct error message is printed for unexpected error
    assert "❌ An unexpected error occurred" in out


# /* jscpd:ignore-end */
