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
    with patch("os.path.exists", return_value=False):
        result = load_cache()
        assert (
            result == {}
        ), "Expected an empty dictionary when the cache file doesn't exist"


def test_acceptance_criteria_no_change_but_invalid(mock_load_cache, mock_save_cache):
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
    class Args:
        issue_key = "AAP-test_edit_with_ai"
        no_ai = False
        lint = False

    cli.validate_issue({})
