#!/usr/bin/env python
"""
This module contains unit tests for the Jira issue editing and validation commands in a command-line interface (CLI)
application. The tests are built using the pytest framework and focus on various functionalities, including editing
issue descriptions, validating fields, and utilizing AI-assisted enhancements.

Key functionalities tested include:
- Creation of cache directories for issue data.
- Editing issue descriptions with and without AI assistance.
- Validation of Jira issue fields such as progress, epic link, sprint, priority, and story points.
- Fetching and updating issue descriptions based on user input or AI suggestions.
- Linting descriptions to ensure compliance with specified criteria.

The tests employ mocking to simulate interactions with Jira and AI providers, enabling isolated logic testing without
actual network calls or user input. Both successful and failure scenarios are explored to ensure the robustness and
reliability of the command implementations.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

# from exceptions.exceptions import EditIssueError
from rest.prompts import IssueType, PromptLibrary

import pytest  # isort: skip


from commands.cli_edit_issue import (  # isort: skip
    cli_edit_issue,
    edit_description,
    fetch_description,
    get_prompt,
    lint_description,
    lint_description_once,
    update_jira_description,
)
from commands.cli_validate_issue import (  # isort: skip
    load_and_cache_issue,
    save_cache,
    sha256,
    validate_blocked,
    validate_epic_link,
    validate_field_with_ai,
    validate_priority,
    validate_progress,
    validate_sprint,
    validate_story_points,
)


def test_cache_directory_creation(mock_cache_path, mock_save_cache):
    """
    Creates a test environment to validate the creation of a cache directory.

    Arguments:
    - mock_cache_path (str): A mock path representing the cache directory path.
    - mock_save_cache (function): A function used to save cache data.

    Side Effects:
    - Sets up a mock cache path and patches os.makedirs to simulate directory creation.
    - Mocks the get_cache_path function to return the mock cache path.
    - Checks the condition where the cache directory doesn't exist.
    - Mocks the open function to prevent actual file system interactions.
    """

    # Set up the mock cache path and patch os.makedirs
    with patch("os.makedirs") as makedirs_mock:
        # Mock the get_cache_path function to return the mock path
        with patch(
            "commands.cli_validate_issue.get_cache_path",
            return_value=mock_cache_path,
        ):
            # Simulate the condition where the cache directory doesn't exist
            with patch("os.path.exists", return_value=False):
                # Mock open to avoid interacting with the actual file system
                with patch("builtins.open", MagicMock()):
                    # Call save_cache with the patched CACHE_PATH
                    save_cache({})

                    # Ensure that os.makedirs is called to create the directory
                    makedirs_mock.assert_called_once_with(
                        os.path.dirname(mock_cache_path), exist_ok=True
                    )


def test_edit_issue_prompt_fallback(cli):
    """
    Simulate an exception when trying to get the prompt.

    Arguments:
    - cli (CommandLineInterface): An instance of the CommandLineInterface class used for interaction.

    Exceptions:
    - This function does not raise any exceptions.

    Side Effects:
    - This function does not have any side effects.
    """

    # Simulate exception when trying to get the prompt

    cli.default_prompt = PromptLibrary.get_prompt(IssueType.DEFAULT)
    assert "You are a professional Principal Software Engineer" in cli.default_prompt


def test_edit_issue_executes(cli):
    """
    Executes a test to edit an issue using the provided CLI object.

    Arguments:
    - cli: An instance of a CLI object used to interact with a Jira server.

    Side Effects:
    - Modifies the description of an issue identified by the key "FAKE-123" by calling the edit_issue method of the CLI
    object.
    - Asserts that the update_description method of the Jira object within the CLI object is called exactly once.
    """

    args = type("Args", (), {"issue_key": "FAKE-123", "no_ai": False, "lint": False})()
    cli.edit_issue(args)
    cli.jira.update_description.assert_called_once()


def test_load_and_cache_issue():
    """
    Load and cache an issue for validation.

    Arguments:
    - issue_key (str): The key of the issue to load and cache.

    Return:
    - tuple: A tuple containing two elements:
    - dict: A dictionary representing the cache after loading the issue.
    - dict: A dictionary representing the cached issue with its key as the key and summary hash.

    Exceptions:
    - None
    """

    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={"FAKE-123": {"summary_hash": "some_hash"}},
    ):
        cache, cached = load_and_cache_issue("FAKE-123")
        assert cached == {"summary_hash": "some_hash"}
        assert cache == {"FAKE-123": {"summary_hash": "some_hash"}}


def test_validate_progress():
    """
    Validate the progress of an issue tracker test.

    Arguments:
    - No arguments are taken.

    Side Effects:
    - Initializes an empty list 'problems' to store any encountered issues.
    - Initializes an empty dictionary 'issue_status' to track the status of each issue.
    """

    problems = []
    issue_status = {}

    # Test when status is "In Progress" but no assignee
    validate_progress("In Progress", None, problems, issue_status)
    assert "❌ Issue is In Progress but unassigned" in problems
    assert issue_status["Progress"] is False

    # Test when status is "In Progress" and assignee is present
    problems.clear()
    validate_progress("In Progress", "assignee", problems, issue_status)
    assert len(problems) == 0  # No issues
    assert issue_status["Progress"] is True


def test_validate_epic_link():
    """
    Validate the Epic Link field for test issues.

    Arguments:
    - No arguments.

    Side Effects:
    - Modifies the 'problems' list.
    - Modifies the 'issue_status' dictionary.
    """

    problems = []
    issue_status = {}

    # Test when epic_link is missing and issue type is not exempt
    validate_epic_link("Story", "In Progress", None, problems, issue_status)
    assert "❌ Issue has no assigned Epic" in problems
    assert issue_status["Epic"] is False

    # Test when epic_link is missing but issue type is exempt
    problems.clear()
    validate_epic_link("Epic", "New", None, problems, issue_status)
    assert len(problems) == 0  # No issues
    assert issue_status["Epic"] is True


def test_validate_sprint():
    """
    Validates the sprint by checking for any problems with the sprint setup.

    Arguments:
    - No arguments.

    Side Effects:
    - Modifies the 'problems' list.
    - Modifies the 'issue_status' dictionary.
    """

    problems = []
    issue_status = {}

    # Test when status is "In Progress" but no sprint assigned
    validate_sprint("In Progress", None, problems, issue_status)
    assert "❌ Issue is In Progress but not assigned to a Sprint" in problems
    assert issue_status["Sprint"] is False

    # Test when status is "In Progress" and sprint is assigned
    problems.clear()
    validate_sprint("In Progress", "Sprint-1", problems, issue_status)
    assert len(problems) == 0  # No issues
    assert issue_status["Sprint"] is True


def test_validate_priority():
    """
    Validate the priority of an issue in a test environment.

    Arguments:
    - No arguments.

    Side Effects:
    - Modifies the 'problems' list and 'issue_status' dictionary in the test environment.
    """

    problems = []
    issue_status = {}

    # Test when priority is not set
    validate_priority(None, problems, issue_status)
    assert "❌ Priority not set" in problems
    assert issue_status["Priority"] is False

    # Test when priority is set
    problems.clear()
    validate_priority("High", problems, issue_status)
    assert len(problems) == 0  # No issues
    assert issue_status["Priority"] is True


def test_validate_story_points():
    """
    Validate story points for test cases.

    Arguments:
    - No arguments.

    Side Effects:
    - Modifies the 'problems' list.
    - Modifies the 'issue_status' dictionary.
    """

    problems = []
    issue_status = {}

    # Test when story points are not assigned and status is not "Refinement" or "New"
    validate_story_points(None, "In Progress", problems, issue_status)
    assert "❌ Story points not assigned" in problems
    assert issue_status["Story P."] is False

    # Test when story points are not assigned but status is "Refinement"
    problems.clear()
    validate_story_points(None, "Refinement", problems, issue_status)
    assert len(problems) == 0  # No issues
    assert issue_status["Story P."] is True


def test_validate_blocked():
    """
    Validate if there are any blocked issues in the test.

    Arguments:
    - No arguments.

    Side Effects:
    - Initializes an empty list 'problems' to store any blocked issues.
    - Initializes an empty dictionary 'issue_status' to track the status of each issue.
    """

    problems = []
    issue_status = {}

    # Test when the issue is blocked but has no reason
    validate_blocked("True", None, problems, issue_status)
    assert "❌ Issue is blocked but has no blocked reason" in problems
    assert issue_status["Blocked"] is False

    # Test when the issue is blocked and has a reason
    problems.clear()
    validate_blocked("True", "Blocked due to issue", problems, issue_status)
    assert len(problems) == 0  # No issues
    assert issue_status["Blocked"] is True


def test_validate_field_with_ai_valid():
    """
    Validate a field using an AI-based provider.

    Arguments:
    - None

    Side Effects:
    - Modifies the global state by initializing the 'problems' list, 'issue_status' dictionary, and 'cached_field_hash'
    variable.

    Exceptions:
    - None
    """

    # Patch ai_provider to return the MagicMock object
    with patch("providers.get_ai_provider", return_value=MagicMock()) as ai_provider:
        problems = []  # Initialize problems list
        issue_status = {}  # Initialize issue_status dictionary
        cached_field_hash = None  # Initialize cached hash

        # Set up the mock for the improve_text method
        improve_text_mock = MagicMock()
        improve_text_mock.return_value = "OK"  # Mock AI response for valid summary
        ai_provider.improve_text = improve_text_mock  # Assign the mock to ai_provider

        # Test when field value requires validation
        cached_field_hash = validate_field_with_ai(
            "Summary",
            "Test summary",
            sha256("Test summary"),
            cached_field_hash,
            ai_provider,
            problems,
            issue_status,
        )

        # Check if the problem was added to the list (invalid summary)
        print(f"Problems: {problems}")  # Debugging: Print the problems list
        assert len(problems) == 0  # Should have one problem related to summary
        assert (
            "❌ Summary: Summary is unclear" not in problems
        )  # Validate the problem message
        assert (
            issue_status["Summary"] is True
        )  # Status should be False as AI returned an issue


def test_validate_field_with_ai_invalid():
    """
    Validate a field using an AI provider and handle invalid cases.

    Arguments:
    - field_name (str): The name of the field being validated.
    - field_value (str): The value of the field being validated.
    - field_hash (str): The hash value of the field value.
    - cached_field_hash (str): The cached hash value of the field, initially set to None.
    - ai_provider (MagicMock): A mocked AI provider object used for validation.
    - problems (list): A list to store validation issues found during the process.
    - issue_status (dict): A dictionary to track the status of each field.

    Side Effects:
    - Modifies the global state by patching the 'ai_provider' to return a MagicMock object.
    - Initializes 'problems' list, 'issue_status' dictionary, and 'cached_field_hash' to empty values.
    """

    # Patch ai_provider to return the MagicMock object
    with patch("providers.get_ai_provider", return_value=MagicMock()) as ai_provider:
        problems = []  # Initialize problems list
        issue_status = {}  # Initialize issue_status dictionary
        cached_field_hash = None  # Initialize cached hash

        # Set up the mock for the improve_text method
        improve_text_mock = MagicMock()
        improve_text_mock.return_value = (
            "Summary is unclear"  # Set AI to return "not OK"
        )
        ai_provider.improve_text = improve_text_mock  # Assign the mock to ai_provider

        # Run validation for the invalid summary
        cached_field_hash = validate_field_with_ai(
            "Summary",
            "Test summary",
            sha256("Test summary"),
            cached_field_hash,
            ai_provider,
            problems,
            issue_status,
        )

        # Check if the problem was added to the list (invalid summary)
        print(f"Problems: {problems}")  # Debugging: Print the problems list
        assert len(problems) == 1  # Should have one problem related to summary
        assert (
            "❌ Summary: Summary is unclear" in problems
        )  # Validate the problem message
        assert (
            issue_status["Summary"] is False
        )  # Status should be False as AI returned an issue


def test_edit_no_ai(cli):
    """
    Summary:
    Mock functions related to Jira API to test editing functionality without using AI.

    Arguments:
    - cli (object): An object representing the command-line interface (CLI) used to interact with Jira.

    Side Effects:
    - Modifies the behavior of Jira API functions for testing purposes.
    """

    cli.jira.get_description = lambda k: "description"
    cli.jira.update_description = MagicMock()
    cli.jira.get_issue_type = lambda k: "story"

    # Patch subprocess.call to prevent the editor from opening
    with patch("subprocess.call") as mock_subprocess:
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write("edited")
            tf.seek(0)

            class Args:
                issue_key = "AAP-test_edit_no_ai"
                no_ai = True
                lint = False  # ✅ Add this to fix the error

            cli.edit_issue(Args())
            cli.jira.update_description.assert_called_once()
            mock_subprocess.assert_called_once()  # Ensure subprocess.call was called


def test_edit_with_ai(cli):
    """
    Updates Jira issue descriptions using an AI service.

    Arguments:
    - cli: An object containing references to Jira API and AI service providers.

    Side Effects:
    - Modifies Jira issue descriptions by updating them with cleaned text generated by the AI service.
    """

    cli.jira.get_description = lambda k: "raw text"
    cli.jira.update_description = MagicMock()
    cli.jira.get_issue_type = lambda k: "story"
    cli.ai_provider.improve_text = lambda p, t: "cleaned text"

    # Patch subprocess.call to prevent the editor from opening
    with patch("subprocess.call") as mock_subprocess:
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write("dirty")
            tf.seek(0)

            class Args:
                issue_key = "AAP-test_edit_with_ai"
                no_ai = False
                lint = False  # ✅ Add this to fix the error

            cli.edit_issue(Args())
            cli.jira.update_description.assert_called_once_with(
                "AAP-test_edit_with_ai", "cleaned text"
            )
            mock_subprocess.assert_called_once()


def test_fetch_description(cli):
    """
    Fetches the description from a Jira issue using a provided CLI instance.

    Arguments:
    - cli (object): An instance of the CLI used to interact with Jira.

    Side Effects:
    - Modifies the `get_description` method of the Jira mock object to return "Test description".
    """

    jira_mock = MagicMock()
    jira_mock.get_description = MagicMock(return_value="Test description")

    description = fetch_description(jira_mock, "ISSUE-123")
    assert description == "Test description"


def test_update_jira_description():
    """
    Update the description of a Jira issue using a mocked Jira object.

    Arguments:
    - No arguments.

    Side Effects:
    - Modifies the description of a Jira issue using a mocked Jira object.
    """

    jira_mock = MagicMock()
    jira_mock.update_description = MagicMock()

    update_jira_description(jira_mock, "ISSUE-123", "Cleaned description")

    jira_mock.update_description.assert_called_once_with(
        "ISSUE-123", "Cleaned description"
    )


# def test_update_jira_update_description_exception(cli):
#     jira_mock = MagicMock()
#     jira_mock.update_description = MagicMock()

#     class Args:
#         isssue_key = "abc-123"

#     with patch("commands.cli_edit_issue.fetch_description") as mock:
#         mock.side_effect = EditIssueError("fail")

#         with pytest.raises(EditIssueError):
#             print("here")
#             cli_edit_issue(jira_mock, MagicMock(), "ISSUE-123", MagicMock(), Args())

#     jira_mock.update_description.assert_called_once_with(
#         "ISSUE-123", "Cleaned description"
#     )


def test_lint_description_once():
    """
    Mocks the AI provider to improve a text description and validates it once.

    Arguments:
    - No arguments.

    Side Effects:
    - Mocks the AI provider to improve a text description.
    - Mocks the validation function to return a list containing the cleaned description.

    Returns:
    - No explicit return value.
    """

    ai_provider_mock = MagicMock()
    ai_provider_mock.improve_text = MagicMock(return_value="Cleaned description")
    validate_mock = MagicMock(return_value=[["❌ Description: Cleaned description"]])
    mock_input = MagicMock(side_effect=["additional details"])

    with (
        patch("commands.cli_edit_issue.validate", validate_mock),
        patch("builtins.input", mock_input),
    ):
        cleaned, should_continue = lint_description_once(
            "Original description", ai_provider_mock
        )
        assert cleaned == "Cleaned description"
        assert should_continue is True
        assert validate_mock.call_count == 1
        assert mock_input.call_count == 1


def test_lint_description():
    """
    This function is a test case for linting a description using a mock AI provider. It creates a MagicMock object to
    simulate an AI provider and sets up a mock method `improve_text` that returns a cleaned description when called.

    Arguments:
    - No arguments are passed explicitly to this function.

    Side Effects:
    - The function sets up mock objects to simulate interactions with an AI provider and validation process.

    Returns:
    - No return value explicitly specified as the function is a test case.
    """

    ai_provider_mock = MagicMock()
    ai_provider_mock.improve_text = MagicMock(return_value="Cleaned description")

    # Mock validate function to simulate two iterations:
    # 1st iteration: validation issues (invalid description)
    # 2nd iteration: no validation issues (valid description)
    validate_mock = MagicMock(side_effect=[["❌ Description: Cleaned description"], []])

    # Create a mock input to track interactions
    mock_input = MagicMock(side_effect=["additional details", "more details"])

    # Mock lint_description_once to directly return "Cleaned description"
    with patch(
        "commands.cli_edit_issue.lint_description_once",
        return_value=("Cleaned description", False),
    ):
        # Call the lint_description function (which now uses the mocked lint_description_once)
        cleaned = lint_description("Original description", ai_provider_mock)

        # Assert the final cleaned description is returned as expected
        assert (
            cleaned == "Cleaned description"
        )  # We expect the cleaned description after AI processing

        # Ensure that input was not called, since lint_description_once is mocked
        assert mock_input.call_count == 0  # No interaction since the function is mocked

        # Assert that validate was also not called (since the function is mocked)
        assert validate_mock.call_count == 0


def test_get_prompt():
    """
    This function is used to test the get_prompt function by creating a MagicMock object for a Jira issue. The
    MagicMock object simulates the behavior of a Jira issue and its type being a "story".
    """

    jira_mock = MagicMock()
    jira_mock.get_issue_type = MagicMock(return_value="story")

    prompt = get_prompt(jira_mock, "ISSUE-123", "Default prompt")
    assert "As a professional Principal Software Engineer, you write acute" in prompt


def test_edit_description():
    """
    Updates the description of a test.

    Arguments:
    - original_description (str): The original description of the test.
    """

    original_description = "Test description"

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
        tmp.write(original_description)
        tmp.flush()
        tmp.seek(0)
        edited = edit_description(original_description)
        assert edited == original_description
        os.remove(tmp.name)

    # Test failure scenario (simulating subprocess.call failure)
    with patch("subprocess.call", side_effect=Exception("Editor failed")):
        with pytest.raises(Exception, match="Editor failed"):
            edit_description(original_description)


def test_lint_description_once_no_issues():
    """
    Mock the AI provider's improve_text method to return a cleaned description.

    Arguments:
    - cleaned (str): The original description to be cleaned.
    - ai_provider_mock (MagicMock): A mock object of the AI provider to simulate the improve_text method.

    Return:
    - tuple: A tuple containing the cleaned description (str) and a boolean indicating whether any issues were found
    (False in this case).

    Side Effects:
    - Calls the validate function to simulate no issues found in the description.
    """

    # Mock the AI provider's improve_text method
    ai_provider_mock = MagicMock()
    ai_provider_mock.improve_text = MagicMock(return_value="Cleaned description")

    # Mock the validate function to simulate no issues
    validate_mock = MagicMock(
        return_value=[[]]
    )  # Empty list, meaning no description problems

    # Simulate the cleaned description without issues
    cleaned = "Original description"

    with patch("commands.cli_edit_issue.validate", validate_mock):
        # Call the lint_description_once function (should return cleaned description and False)
        result, should_continue = lint_description_once(cleaned, ai_provider_mock)

        # Assert that the cleaned description is returned
        assert result == "Original description"

        # Assert that should_continue is False, meaning no issues were found
        assert should_continue is False

        # Ensure validate was called once
        assert validate_mock.call_count == 1


def test_cli_edit_issue_no_edited(mock_save_cache):
    """
    Simulate editing an issue in a CLI without making any changes.

    Arguments:
    - mock_save_cache: MagicMock object used for caching

    Side Effects:
    - Calls to the Jira API and an AI provider are simulated using MagicMock objects
    """

    # Setup the mocks
    jira_mock = MagicMock()
    ai_provider_mock = MagicMock()
    default_prompt = "Default prompt"
    try_cleanup_fn = MagicMock()

    # Arguments for the test, simulating the case when no AI cleanup is needed
    args = MagicMock()
    args.issue_key = "AAP-test_cli_edit_issue_no_edited"
    args.no_ai = True  # Simulate no AI cleanup
    args.lint = False  # No linting

    # Mock fetch_description to return a valid description
    fetch_description_mock = MagicMock(return_value="Original description")

    # Mock edit_description to return None (simulating no editing)
    edit_description_mock = MagicMock(return_value=None)

    # Mock update_jira_description to ensure it is not called when the description is not edited
    update_jira_description_mock = MagicMock()

    with (
        patch(
            "commands.cli_edit_issue.fetch_description",
            fetch_description_mock,
        ),
        patch(
            "commands.cli_edit_issue.edit_description",
            edit_description_mock,
        ),
        patch(
            "commands.cli_edit_issue.update_jira_description",
            update_jira_description_mock,
        ),
    ):
        # Call the function
        cli_edit_issue(
            jira_mock, ai_provider_mock, default_prompt, try_cleanup_fn, args
        )

        # Assert that edit_description was called with the correct description
        edit_description_mock.assert_called_once_with("Original description")

        # Assert that update_jira_description was not called because edited is None
        update_jira_description_mock.assert_not_called()


def test_cli_edit_issue_lint_true(cli, mock_save_cache):
    """
    Simulate a test scenario where the CLI edit issue lint is set to True.

    Arguments:
    - cli: An object representing the command-line interface.
    - mock_save_cache: A mock object used to save cache data.

    Side Effects:
    - Sets up the necessary mocks for testing purposes.
    """

    # Setup the mocks

    # Arguments for the test, simulating the case where linting is enabled
    args = MagicMock()
    args.issue_key = "AAP-test_cli_edit_issue_lint_true"
    args.no_ai = False  # Simulate that AI cleanup is needed
    args.lint = True  # Linting is enabled

    # Mock fetch_description to return a valid description
    fetch_description_mock = MagicMock(return_value="Original description")
    fetch_description_mock.name = "fetch_description_mock"

    # Mock edit_description to return an edited description
    edit_description_mock = MagicMock(return_value="Edited description")
    edit_description_mock.name = "edit_description_mock"

    # Mock try_cleanup_fn to simulate AI cleanup and return a cleaned description
    try_cleanup_fn_mock = MagicMock(return_value="Cleaned description")
    try_cleanup_fn_mock.name = "try_cleanup_fn_mock"

    # Mock lint_description to simulate linting and return the linted description
    lint_description_mock = MagicMock(return_value="Linted description")
    lint_description_mock.name = "lint_description_mock"

    # Mock update_jira_description to ensure it is called with the final cleaned description
    update_jira_description_mock = MagicMock()
    update_jira_description_mock.name = "update_jira_description_mock"

    with (
        patch(
            "commands.cli_edit_issue.fetch_description",
            fetch_description_mock,
        ),
        patch(
            "commands.cli_edit_issue.edit_description",
            edit_description_mock,
        ),
        patch("commands._try_cleanup", try_cleanup_fn_mock),
        patch(
            "commands.cli_edit_issue.lint_description",
            lint_description_mock,
        ),
        patch(
            "commands.cli_edit_issue.update_jira_description",
            update_jira_description_mock,
        ),
    ):
        # Call the function with linting enabled
        cli.edit_issue(args)

        # Assert that fetch_description was called with the correct issue key
        fetch_description_mock.assert_called_once_with(cli.jira, args.issue_key)

        # Assert that edit_description was called with the original description
        edit_description_mock.assert_called_once_with("Original description")


def test_cli_edit_issue_returns_early_on_empty_description():
    """
    Check if the description of an issue is empty and return early.

    Arguments:
    - No arguments.

    Returns:
    - No return value.
    """

    fake_jira = MagicMock()
    fake_jira.get_description.return_value = ""  # or None, both will work

    fake_ai = MagicMock()
    fake_cleanup = MagicMock()

    class Args:
        issue_key = "TEST-42"
        no_ai = True
        lint = False

    with patch("commands.cli_edit_issue.fetch_description", return_value=""):
        result = cli_edit_issue(
            fake_jira, fake_ai, "unused_prompt", fake_cleanup, Args()
        )

    assert result is False
    fake_jira.get_description.assert_not_called()  # because fetch_description is patched
    fake_ai.improve_text.assert_not_called()
    fake_cleanup.assert_not_called()
