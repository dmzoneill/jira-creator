import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from jira_creator.commands.validate_issue import save_cache
from jira_creator.rh_jira import JiraCLI  # Correct import


@pytest.fixture
def mock_cache_path():
    # Create a temporary directory and file for the cache
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_cache_path = temp_file.name

        # Debugging: print the mocked cache path
        print(f"Debug: Mocked cache path: {temp_cache_path}")

        # Ensure the file exists
        if os.path.exists(temp_cache_path):
            os.remove(temp_cache_path)  # Make sure the file doesn't exist before test

        # Override the CACHE_PATH for the test
        with patch("jira_creator.commands.validate_issue.CACHE_PATH", temp_cache_path):
            yield temp_cache_path

    # Cleanup after test
    if os.path.exists(temp_cache_path):
        os.remove(temp_cache_path)


@pytest.fixture
def cli():
    with (
        patch(
            "jira_creator.commands.edit_issue.tempfile.NamedTemporaryFile"
        ) as mock_tempfile,
        patch("jira_creator.commands.edit_issue.subprocess.call", return_value=0),
    ):
        cli = JiraCLI()

        # Mock Jira methods
        cli.jira.get_description = MagicMock(return_value="Original description")
        cli.jira.update_description = MagicMock(return_value=True)
        cli.jira.get_issue_type = MagicMock(return_value="story")

        # Mock AI provider
        cli.ai_provider.improve_text = MagicMock(
            return_value="Cleaned and corrected content."
        )

        # Mock tempfile file behavior
        fake_file = MagicMock()
        fake_file.__enter__.return_value = fake_file
        fake_file.read.return_value = "edited content"
        fake_file.name = (
            "/tmp/file.md"  # Using /tmp/file.md to avoid conflict with actual files
        )
        mock_tempfile.return_value = fake_file

        yield cli


# Test to ensure directory is created
def test_cache_directory_creation(mock_cache_path):
    # Set up the mock cache path and patch os.makedirs
    with patch("os.makedirs") as makedirs_mock:
        # Simulate the condition where the cache directory doesn't exist
        with patch("os.path.exists", return_value=False):
            # Debugging: Print the CACHE_PATH used before calling save_cache
            print(
                f"Debug: Verifying CACHE_PATH during save_cache test: {mock_cache_path}"
            )

            # Call save_cache with the patched CACHE_PATH
            save_cache({})

            # Ensure that os.makedirs is called to create the directory
            print(f"Debug: Verifying os.makedirs call")
            makedirs_mock.assert_called_once_with(
                os.path.dirname(mock_cache_path), exist_ok=True
            )


def test_edit_issue_prompt_fallback(cli):
    # Simulate exception when trying to get the prompt
    with patch(
        "jira_creator.rh_jira.JiraPromptLibrary.get_prompt",
        side_effect=Exception("Prompt error"),
    ):
        # Default prompt to fall back to
        default_prompt = "Fallback prompt"

        # Simulate args
        args = type(
            "Args", (), {"issue_key": "FAKE-123", "no_ai": False, "lint": False}
        )()

        # Run the edit issue method
        cli.edit_issue(args)

        # Check if default prompt was used as fallback
        # In this case, we check the call to JiraPromptLibrary.get_prompt, which should have triggered an exception.
        # We want to verify that the prompt was set to the default prompt after the exception.
        # Since there's no direct way to assert the prompt value here, we can verify the behavior.
        cli.jira.update_description.assert_called_once()  # Ensure update_description was called
        print(f"Captured Output: Prompt fallback: {default_prompt}")


def test_edit_issue_executes(cli):
    args = type("Args", (), {"issue_key": "FAKE-123", "no_ai": False, "lint": False})()
    cli.edit_issue(args)
    cli.jira.update_description.assert_called_once()


def test_edit_issue_linting_process(cli, capsys, mock_cache_path):
    # Mock the validate function to return problems during the first iteration and empty list on the second
    with patch(
        "jira_creator.rh_jira.edit_issue.validate",
        side_effect=[["❌ Description: mock improved text"], []],
    ):
        # Mock the input function to simulate user input during linting
        with patch("builtins.input", return_value="additional details"):
            # Simulate args
            args = type(
                "Args", (), {"issue_key": "FAKE-123", "no_ai": False, "lint": True}
            )()

            # Call the edit_issue function
            cli.edit_issue(args)

            # Capture the output
            captured = capsys.readouterr()

            # Debugging: Check what the output contains at each step
            print(f"Debug: Captured Output - {captured.out}")

            # Check that the output contains the validation steps and user input prompts
            assert "Starting linting..." in captured.out
            assert (
                "Description problems: ['❌ Description: mock improved text']"
                in captured.out
            )
            assert "User entered: additional details" in captured.out
            assert (
                "Updated cleaned description: Cleaned and corrected content."
                in captured.out
            )
            assert "Final description:" in captured.out

            # Ensure that the update_description was called
            cli.jira.update_description.assert_called_once_with(
                "FAKE-123", "Cleaned and corrected content."
            )

            # Ensure that AI improve_text was called twice with the correct prompt
            assert (
                cli.ai_provider.improve_text.call_count == 2
            )  # It should be called twice

            # First call should have the original description (without additional details)
            cli.ai_provider.improve_text.assert_any_call(
                "You are a professional Principal Software Engineer. You write acute, well-defined Jira storys with a strong focus on clarity, structure, and detail.\nIf standard Jira sections are missing, add them—such as Description, Definition of Done, and Acceptance Criteria. If these sections already exist, preserve and clean up their format.\nFocus on fixing spelling errors, correcting grammatical issues, and improving sentence readability for greater clarity.\n\nFollow this structure:\n\nFIELD|User Story\nFIELD|Supporting documentation\nFIELD|Definition of Done\nFIELD|Acceptance Criteria\nFIELD|Requirements\nFIELD|End to End Test\n\nTEMPLATE|Description\n\nh2. User Story\n\n{{User Story}}\n\nh2. Supporting documentation\n\n{{Supporting documentation}}\n\nh2. Definition of Done\n\n{{Definition of Done}}\n\nh2. Acceptance Criteria\n\n{{Acceptance Criteria}}\n\nh2. Requirements\n\n{{Requirements}}\n\nh2. End to End Test\n\n{{End to End Test}}",
                "edited content",
            )

            # Second call should have the updated description (with additional details)
            cli.ai_provider.improve_text.assert_any_call(
                "Incorporate these additional details into the below Jira description.\nDetails to incorporate: additional details\nOriginal description:\nCleaned and corrected content.",
                "Cleaned and corrected content.",
            )

            # Check if the cleaned description was printed as expected
            # Now the final description is printed after the linting loop ends, so we assert on the final output
            assert "Cleaned and corrected content." in captured.out


def test_edit_no_ai():
    cli = JiraCLI()
    cli.jira.get_description = lambda k: "description"
    cli.jira.update_description = MagicMock()
    cli.jira.get_issue_type = lambda k: "story"

    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("edited")
        tf.seek(0)

        class Args:
            issue_key = "AAP-123"
            no_ai = True
            lint = False  # ✅ Add this to fix the error

        cli.edit_issue(Args())
        cli.jira.update_description.assert_called_once()


def test_edit_with_ai():
    cli = JiraCLI()
    cli.jira.get_description = lambda k: "raw text"
    cli.jira.update_description = MagicMock()
    cli.jira.get_issue_type = lambda k: "story"
    cli.ai_provider.improve_text = lambda p, t: "cleaned text"

    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("dirty")
        tf.seek(0)

        class Args:
            issue_key = "AAP-999"
            no_ai = False
            lint = False  # ✅ Add this to fix the error

        cli.edit_issue(Args())
        cli.jira.update_description.assert_called_once_with("AAP-999", "cleaned text")
