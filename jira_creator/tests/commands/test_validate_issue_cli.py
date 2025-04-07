from unittest.mock import MagicMock, patch

from core.env_fetcher import EnvFetcher

from commands.cli_validate_issue import (  # isort: skip
    cli_validate_issue,
    load_cache,
    sha256,
)


def test_load_cache_file_not_found():
    # Patch os.path.exists to return False, simulating the cache file being absent
    with patch("os.path.exists", return_value=False):
        # Call load_cache, it should return an empty dictionary when the file doesn't exist
        result = load_cache()

        # Assert that the result is an empty dictionary
        assert (
            result == {}
        ), "Expected an empty dictionary when the cache file doesn't exist"


def test_acceptance_criteria_no_change_but_invalid(mock_load_cache, mock_save_cache):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = (
        "Needs Improvement"  # Simulate AI returning a poor response
    )

    # Ensure we add the 'key' field for the issue to match the cache
    fields = {
        "key": "AAP-test_acceptance_criteria_no_change_but_invalid",  # Issue key is added here
        "summary": "Test Summary",
        "description": "Test Description",
        EnvFetcher.get(
            "JIRA_ACCEPTANCE_CRITERIA_FIELD"
        ): "Acceptance criteria description",  # Acceptance criteria field
        EnvFetcher.get("JIRA_EPIC_FIELD"): "Epic Link",
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        "status": {"name": "To Do"},
    }

    # Simulate an existing cached value with last AI acceptance criteria not being "OK"
    cached_data = {
        "last_ai_acceptance_criteria": "Needs Improvement",  # Simulating a poor AI suggestion
        "acceptance_criteria_hash": sha256(
            "kill cache"
        ),  # Hash of the acceptance criteria
        "last_ai_description": "Ok",  # Simulating a poor AI suggestion
        # /* jscpd:ignore-tart */
        "description_hash": sha256(fields["description"]),  # Hash of the description
        "last_ai_summary": "Ok",  # Simulating a poor AI suggestion
        "summary_hash": sha256(fields["summary"]),  # Hash of the description
    }

    # Patch the cache loading function to return the mocked cached data
    with patch(
        "commands.cli_validate_issue.save_cache"
    ):
        with patch(
            "commands.cli_validate_issue.load_cache",
            return_value={fields["key"]: cached_data},
        ):
            problems = cli_validate_issue(fields, ai_provider)[0]
            # /* jscpd:ignore-end */
            # Assert that the invalid acceptance criteria was detected
            assert (
                "❌ Acceptance Criteria: Needs Improvement" in problems
            )  # The old AI suggestion should be used
            assert (
                "❌ Acceptance Criteria: Check the quality of the following Jira acceptance criteria."
                not in problems
            )  # No new AI review should be triggered


def test_validate_issue_delegation(mock_save_cache, cli, capsys):
    # Create a MagicMock instance for validate_issue
    mock_validate_issue = MagicMock(return_value=("mocked result", []))
    with patch("rh_jira.cli_validate_issue", mock_validate_issue):
        fields = {
            "summary": "Test",
            "description": "Something",
        }  # Add "key" to ensure the condition is not met early

        # Call the method in JiraCLI that calls the patched validate_issue
        cli.validate_issue(fields)

        # Debugging: Check if the mock was called and with what arguments
        print(
            f"Mock called: {mock_validate_issue.call_count}"
        )  # Check how many times the mock was called
        print(
            f"Arguments passed to mock: {mock_validate_issue.call_args}"
        )  # Check the arguments passed to the mock

        # Assert that validate_issue was called with the expected arguments
        mock_validate_issue.assert_called_once_with(fields, cli.ai_provider)


def test_acceptance_criteria_validation(mock_save_cache, cli, capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # Simulate AI's 'OK' response

    fields = {
        "key": "AAP-test_acceptance_criteria_validation",
        "summary": "Test Summary",
        "description": "Test Description",
        EnvFetcher.get(
            "JIRA_ACCEPTANCE_CRITERIA_FIELD"
        ): "Acceptance criteria description",  # Acceptance criteria field
        EnvFetcher.get("JIRA_EPIC_FIELD"): "Epic Link",
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        "status": {"name": "To Do"},
    }

    # Mock the cache load to simulate an existing cache with the previous hash
    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={fields["key"]: {"acceptance_criteria_hash": "old_hash"}},
    ):
        problems = cli_validate_issue(fields, ai_provider)[0]

        # Assert that the validation message is correct
        assert [] == problems  # Since the AI returns OK, there should be no error


def test_no_issue_key_return(mock_save_cache, cli, capsys):
    # Create a 'fields' dictionary without an issue key
    fields = {
        "summary": "Test Summary",
        "description": "Test Description",
        EnvFetcher.get(
            "JIRA_ACCEPTANCE_CRITERIA_FIELD"
        ): "Acceptance criteria description",  # Acceptance criteria field
        EnvFetcher.get("JIRA_EPIC_FIELD"): "Epic Link",
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        "status": {"name": "To Do"},
    }

    # Simulate the AI provider (no need for specific behavior here)
    ai_provider = MagicMock()

    # Call the function and assert that problems and issue_status are returned as empty
    problems, issue_status = cli_validate_issue(fields, ai_provider)

    # Assert that the return is an empty problems list and empty issue_status
    assert problems == []
    assert issue_status == {}


def test_acceptance_criteria_no_change(mock_save_cache, cli, capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # Simulate AI returning "OK"

    fields = {
        "key": "AAP-test_acceptance_criteria_no_change",
        "summary": "Test Summary",
        "description": "Test Description",
        EnvFetcher.get(
            "JIRA_ACCEPTANCE_CRITERIA_FIELD"
        ): "Acceptance criteria description",  # Acceptance criteria field
        EnvFetcher.get("JIRA_EPIC_FIELD"): "Epic Link",
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        "status": {"name": "To Do"},
    }

    # Simulate an existing cached value with last AI acceptance criteria
    cached_data = {
        "last_ai_acceptance_criteria": "OK",
        "acceptance_criteria_hash": sha256(
            fields[EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD")]
        ),
    }

    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={fields["key"]: cached_data},
    ):
        problems = cli_validate_issue(fields, ai_provider)[0]

        # Check that no new AI suggestion is made since acceptance criteria hasn't changed
        assert [] == problems


def test_description_no_change_but_invalid(mock_save_cache, cli, capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = (
        "Needs Improvement"  # Simulate AI returning a poor response
    )

    # Ensure we add the 'key' field for the issue to match the cache
    fields = {
        "key": "AAP-test_description_no_change_but_invalid",  # Issue key is added here
        "summary": "Test Summary",
        "description": "Test Description",  # The description is used
        EnvFetcher.get(
            "JIRA_ACCEPTANCE_CRITERIA_FIELD"
        ): "Acceptance criteria description",
        EnvFetcher.get("JIRA_EPIC_FIELD"): "Epic Link",
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        "status": {"name": "To Do"},
    }

    # Simulate an existing cached value with last AI description not being "OK"
    cached_data = {
        "last_ai_description": "Needs Improvement",  # Simulating a poor AI suggestion
        "description_hash": sha256(fields["description"]),  # Hash of the description
    }

    cached_data = {
        "last_ai_acceptance_criteria": "Ok",  # Simulating a poor AI suggestion
        "acceptance_criteria_hash": sha256(
            fields[EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD")]
        ),  # Hash of the acceptance criteria
        # /* jscpd:ignore-start */
        "last_ai_description": "Needs Improvement",  # Simulating a poor AI suggestion
        "description_hash": sha256("kill cache"),  # Hash of the description
        "last_ai_summary": "Ok",  # Simulating a poor AI suggestion
        "summary_hash": sha256(fields["summary"]),  # Hash of the description
        # /* jscpd:ignore-end */
    }

    # Patch the cache loading function to return the mocked cached data
    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={fields["key"]: cached_data},
    ):
        # Patch the cache loading function to return the mocked cached data
        with patch(
            "commands.cli_validate_issue.save_cache"
        ) as mock_save_save_cache:
            problems = cli_validate_issue(fields, ai_provider)[0]

            # Assert that the invalid description was detected
            assert (
                "❌ Description: Needs Improvement" in problems
            )  # The old AI suggestion should be used
            assert (
                "❌ Description: Check the quality of the following Jira description."
                not in problems
            )  # No new AI review should be triggered


def test_story_without_epic_flagged(mock_save_cache, cli, capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # ✅ Mocked correctly

    fields = {
        "key": "AAP-test_story_without_epic_flagged",
        "issuetype": {"name": "Story"},
        "status": {"name": "In Progress"},
        "summary": "Some summary",
        "description": "Some description",
        EnvFetcher.get("JIRA_EPIC_FIELD"): None,  # Epic link missing
        EnvFetcher.get("JIRA_SPRINT_FIELD"): None,
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
        EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
        "assignee": {"displayName": "Alice"},
    }

    problems = cli_validate_issue(fields, ai_provider)[0]

    assert "❌ Issue has no assigned Epic" in problems
