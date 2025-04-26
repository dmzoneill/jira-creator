#!/usr/bin/env python
"""
This module provides unit tests for the command-line interface (CLI) validation of Jira issues, specifically focusing
on the acceptance criteria and description validation. It includes functions to generate common fields and cached data
for testing purposes. The tests verify the correct behavior of the validation functions against various scenarios.

Key functions and classes:
- `generate_fields`: Generates a dictionary of common fields for a Jira issue.
- `generate_cached_data`: Creates a dictionary simulating cached validation data.
- `test_load_cache_file_not_found`: Tests the behavior of loading a cache file that does not exist.
- `test_acceptance_criteria_no_change_but_invalid`: Tests the validation of acceptance criteria when no changes are
made but the criteria is invalid.
- `test_acceptance_criteria_validation`: Validates acceptance criteria when the criteria is considered acceptable.
- `test_description_no_change_but_invalid`: Tests the validation of descriptions when no changes are made but the
description is invalid.
- `test_cli_validate_issue`: Tests the CLI interface for validating Jira issues.

This module uses the `unittest.mock` library to mock dependencies and the behavior of external functions, ensuring that
the tests run in isolation and do not depend on external states.
"""

from unittest.mock import MagicMock, patch

from commands.cli_validate_issue import cli_validate_issue, load_cache, sha256
from core.env_fetcher import EnvFetcher


# Define a helper function for generating common fields
def generate_fields(
    issue_key,
    summary="Test Summary",
    description="Test Description",
    acceptance_criteria="Test Acceptance Criteria",
):
    """
    Generate a dictionary with fields for a JIRA issue.

    Arguments:
    - issue_key (str): The key of the JIRA issue.
    - summary (str): The summary of the JIRA issue (default is "Test Summary").
    - description (str): The description of the JIRA issue (default is "Test Description").
    - acceptance_criteria (str): The acceptance criteria of the JIRA issue (default is "Test Acceptance Criteria").

    Return:
    - dict: A dictionary containing the JIRA fields for the issue.

    Side Effects:
    - Uses the EnvFetcher class to retrieve certain field values from the environment.
    """
    return {
        "key": issue_key,
        "summary": summary,
        "description": description,
        EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"): acceptance_criteria,
        EnvFetcher.get("JIRA_EPIC_FIELD"): "Epic Link",
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        "status": {"name": "To Do"},
    }


# Define a helper function for generating cached data


def generate_cached_data(
    fields,
    description_hash=None,
    summary_hash=None,
    acceptance_criteria_hash=None,
    acceptance_criteria_value=None,
    description_value=None,
):
    """
    Generates cached data hashes based on input fields.

    Arguments:
    - fields (dict): A dictionary containing various field values.
    - description_hash (str, optional): The hash value of the description field. Defaults to None.
    - summary_hash (str, optional): The hash value of the summary field. Defaults to None.
    - acceptance_criteria_hash (str, optional): The hash value of the acceptance criteria field. Defaults to None.
    - acceptance_criteria_value (str, optional): The value of the acceptance criteria field. Defaults to None.
    - description_value (str, optional): The value of the description field. Defaults to None.

    Side Effects:
    - Modifies the input hash values if they are None by calculating the hash of corresponding field values.
    """

    if description_hash is None:
        description_hash = sha256(fields["description"])
    if summary_hash is None:
        summary_hash = sha256(fields["summary"])
    if acceptance_criteria_hash is None:
        acceptance_criteria_hash = sha256(
            fields[EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD")]
        )

    # Ensure that description_value is used if passed
    description_value = description_value or "Needs Improvement"
    acceptance_criteria_value = acceptance_criteria_value or "Needs Improvement"

    return {
        "last_ai_acceptance_criteria": acceptance_criteria_value,
        "acceptance_criteria_hash": acceptance_criteria_hash,
        "last_ai_description": description_value,
        "description_hash": description_hash,
        "last_ai_summary": "Ok",
        "summary_hash": summary_hash,
    }


def test_load_cache_file_not_found():
    """
    Generate a dictionary with fields for a JIRA issue.

    Arguments:
    - issue_key (str): The key of the JIRA issue.
    - summary (str): The summary of the JIRA issue (default is "Test Summary").
    - description (str): The description of the JIRA issue (default is "Test Description").
    - acceptance_criteria (str): The acceptance criteria of the JIRA issue (default is "Test Acceptance Criteria").

    Return:
    - dict: A dictionary containing the JIRA fields for the issue.

    Side Effects:
    - Uses the EnvFetcher class to retrieve certain field values from the environment.
    """

    with patch("os.path.exists", return_value=False):
        result = load_cache()
        assert (
            result == {}
        ), "Expected an empty dictionary when the cache file doesn't exist"


def test_acceptance_criteria_no_change_but_invalid(mock_load_cache, mock_save_cache):
    """
    Simulate a test scenario where the acceptance criteria are not changed, but the provided data is invalid.

    Arguments:
    - mock_load_cache: A mock object for loading cache data.
    - mock_save_cache: A mock object for saving cache data.

    Side Effects:
    - Calls the 'improve_text' method of a MagicMock object representing an AI provider with a return value of "Needs
    Improvement".
    """

    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "Needs Improvement"

    fields = generate_fields(
        "AAP-test_acceptance_criteria_no_change_but_invalid",
        acceptance_criteria="Needs Improvement",
    )
    cached_data = generate_cached_data(fields)

    with patch("commands.cli_validate_issue.save_cache"):
        with patch(
            "commands.cli_validate_issue.load_cache",
            return_value={fields["key"]: cached_data},
        ):
            problems = cli_validate_issue(fields, ai_provider)[0]
            assert "❌ Acceptance Criteria: Needs Improvement" in problems
            assert (
                "❌ Acceptance Criteria: Check the quality of the following Jira acceptance criteria."
                not in problems
            )


def test_acceptance_criteria_validation(mock_save_cache, cli, capsys):
    """
    Validate the acceptance criteria for a test case.

    Arguments:
    - mock_save_cache: MagicMock object for saving cache data.
    - cli: Command Line Interface (CLI) object for interacting with the command line.
    - capsys: Pytest fixture for capturing stdout and stderr outputs.

    Side Effects:
    - Sets up a MagicMock object 'ai_provider' for AI text improvement with a return value of "OK".
    """

    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"

    fields = generate_fields("AAP-test_acceptance_criteria_validation")

    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={fields["key"]: {"acceptance_criteria_hash": "old_hash"}},
    ):
        problems = cli_validate_issue(fields, ai_provider)[0]
        assert [] == problems


def test_description_no_change_but_invalid(mock_save_cache, cli, capsys):
    """
    Simulate a test scenario where a mock AI provider is used to improve text, returning "Needs Improvement".

    Arguments:
    - mock_save_cache: A mock object for saving cache data.
    - cli: Command Line Interface object.
    - capsys: Pytest fixture capturing stdout and stderr output.

    Side Effects:
    - Calls the `improve_text` method on a mock AI provider object.

    Return: N/A
    """

    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "Needs Improvement"

    fields = generate_fields(
        "AAP-test_description_no_change_but_invalid", description="Needs Improvement"
    )
    cached_data = generate_cached_data(
        fields, acceptance_criteria_value="Needs Improvement"
    )

    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={fields["key"]: cached_data},
    ):
        with patch("commands.cli_validate_issue.save_cache") as _:
            problems = cli_validate_issue(fields, ai_provider)[0]
            # Now check for "Description" since we correctly set the description in the cached data
            assert "❌ Description: Needs Improvement" in problems
            assert (
                "❌ Description: Check the quality of the following Jira description."
                not in problems
            )


def test_cli_validate_issue(cli):
    """
    Validate the CLI input for testing purposes.

    Arguments:
    - cli: An instance of the CLI object.

    Side Effects:
    - Modifies the Args class attributes for issue_key, no_ai, and lint.
    """

    class Args:
        issue_key = "AAP-test_edit_with_ai"
        no_ai = False
        lint = False

    cli.validate_issue({})
