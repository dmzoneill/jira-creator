import os
from unittest.mock import ANY, MagicMock, patch

from commands import validate_issue

from jira_creator.rh_jira import JiraCLI

CACHE_PATH = os.path.expanduser("~/.config/rh-issue/ai-hashes.json")


def test_load_cache_file_not_found():
    # Patch os.path.exists to return False, simulating the cache file being absent
    with patch("os.path.exists", return_value=False):
        # Call load_cache, it should return an empty dictionary when the file doesn't exist
        result = validate_issue.load_cache()

        # Assert that the result is an empty dictionary
        assert (
            result == {}
        ), "Expected an empty dictionary when the cache file doesn't exist"


def test_acceptance_criteria_no_change_but_invalid(capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = (
        "Needs Improvement"  # Simulate AI returning a poor response
    )

    # Ensure we add the 'key' field for the issue to match the cache
    fields = {
        "key": "AAP-100",  # Issue key is added here
        "summary": "Test Summary",
        "description": "Test Description",
        "customfield_12315940": "Acceptance criteria description",  # Acceptance criteria field
        "customfield_12311140": "Epic Link",
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "status": {"name": "To Do"},
    }

    # Simulate an existing cached value with last AI acceptance criteria not being "OK"
    cached_data = {
        "last_ai_acceptance_criteria": "Needs Improvement",  # Simulating a poor AI suggestion
        "acceptance_criteria_hash": validate_issue.sha256(
            fields["customfield_12315940"]
        ),  # Hash of the acceptance criteria
    }

    # Patch the cache loading function to return the mocked cached data
    with patch(
        "commands.validate_issue.load_cache", return_value={fields["key"]: cached_data}
    ):
        problems = validate_issue.handle(fields, ai_provider)

        # Assert that the invalid acceptance criteria was detected
        assert (
            "❌ Acceptance Criteria: Needs Improvement" in problems
        )  # The old AI suggestion should be used
        assert (
            "❌ Acceptance Criteria: Check the quality of the following Jira acceptance criteria."
            not in problems
        )  # No new AI review should be triggered


@patch("commands.validate_issue.handle")
def test_validate_issue_delegation(mock_handle):
    cli = JiraCLI()
    fields = {"summary": "Test", "description": "Something"}

    cli.validate_issue(fields)

    mock_handle.assert_called_once_with(fields, ANY)


def test_acceptance_criteria_validation(capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # Simulate AI's 'OK' response

    fields = {
        "key": "AAP-100",
        "summary": "Test Summary",
        "description": "Test Description",
        "customfield_12315940": "Acceptance criteria description",  # Acceptance criteria field
        "customfield_12311140": "Epic Link",
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "status": {"name": "To Do"},
    }

    # Mock the cache load to simulate an existing cache with the previous hash
    with patch(
        "commands.validate_issue.load_cache",
        return_value={fields["key"]: {"acceptance_criteria_hash": "old_hash"}},
    ):
        problems = validate_issue.handle(fields, ai_provider)

        # Assert that the validation message is correct
        assert [] == problems  # Since the AI returns OK, there should be no error


def test_acceptance_criteria_no_change(capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # Simulate AI returning "OK"

    fields = {
        "key": "AAP-100",
        "summary": "Test Summary",
        "description": "Test Description",
        "customfield_12315940": "Acceptance criteria description",  # Acceptance criteria field
        "customfield_12311140": "Epic Link",
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "status": {"name": "To Do"},
    }

    # Simulate an existing cached value with last AI acceptance criteria
    cached_data = {
        "last_ai_acceptance_criteria": "OK",
        "acceptance_criteria_hash": validate_issue.sha256(
            fields["customfield_12315940"]
        ),
    }

    with patch(
        "commands.validate_issue.load_cache", return_value={fields["key"]: cached_data}
    ):
        problems = validate_issue.handle(fields, ai_provider)

        # Check that no new AI suggestion is made since acceptance criteria hasn't changed
        assert [] == problems


def test_description_no_change_but_invalid(capsys):
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = (
        "Needs Improvement"  # Simulate AI returning a poor response
    )

    # Ensure we add the 'key' field for the issue to match the cache
    fields = {
        "key": "AAP-100",  # Issue key is added here
        "summary": "Test Summary",
        "description": "Test Description",  # The description is used
        "customfield_12315940": "Acceptance criteria description",
        "customfield_12311140": "Epic Link",
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "status": {"name": "To Do"},
    }

    # Simulate an existing cached value with last AI description not being "OK"
    cached_data = {
        "last_ai_description": "Needs Improvement",  # Simulating a poor AI suggestion
        "description_hash": validate_issue.sha256(
            fields["description"]
        ),  # Hash of the description
    }

    # Patch the cache loading function to return the mocked cached data
    with patch(
        "commands.validate_issue.load_cache", return_value={fields["key"]: cached_data}
    ):
        problems = validate_issue.handle(fields, ai_provider)

        # Assert that the invalid description was detected
        assert (
            "❌ Description: Needs Improvement" in problems
        )  # The old AI suggestion should be used
        assert (
            "❌ Description: Check the quality of the following Jira description."
            not in problems
        )  # No new AI review should be triggered


def test_cache_directory_creation():
    # Set up the mock cache path and patch os.makedirs
    with patch("os.makedirs") as makedirs_mock:
        # Simulate the condition where the cache directory doesn't exist
        with patch("os.path.exists", return_value=False):
            # Call the method that checks and creates the directory
            validate_issue.save_cache({})

            # Ensure that os.makedirs is called to create the directory
            makedirs_mock.assert_called_once_with(
                os.path.dirname(CACHE_PATH), exist_ok=True
            )


def test_story_without_epic_flagged():
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # ✅ Mocked correctly

    fields = {
        "issuetype": {"name": "Story"},
        "status": {"name": "To Do"},
        "summary": "Some summary",
        "description": "Some description",
        "customfield_10008": None,  # Epic link missing
        "customfield_12310940": None,
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "customfield_12316543": {"value": "False"},
        "customfield_12316544": "",
        "assignee": {"displayName": "Alice"},
    }

    problems = validate_issue.handle(fields, ai_provider)

    assert "❌ Issue has no assigned Epic" in problems
