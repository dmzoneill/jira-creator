from unittest.mock import MagicMock, patch

from jira_creator.rh_jira import JiraCLI


def test_edit_prompt_fallback():
    cli = JiraCLI()

    # Mock JiraClient methods
    cli.jira.get_description = MagicMock(return_value="")
    cli.jira.get_issue_type = MagicMock(side_effect=Exception("fail"))
    cli.jira.update_description = MagicMock(return_value=None)

    # Create a dummy temporary file class
    class DummyTempFile:
        pass

    # Patch the tempfile.NamedTemporaryFile method
    cli.jira._tempfile = DummyTempFile

    # Create Args object and run the edit_issue method
    class Args:
        issue_key = "AAP-1"
        no_ai = True

    cli.edit_issue(Args())


def test_edit_issue_prompt_fallback():
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.default_prompt = "fallback prompt"

    # Set up mocks
    cli.jira.get_description.return_value = "original text"
    cli.jira.get_issue_type.return_value = "unknown"

    # Create Args mock
    args = MagicMock()
    args.issue_key = "JIRA-123"

    # Mock editor interaction
    mock_tempfile = MagicMock()
    mock_tempfile.name = "/fake/file.md"
    mock_tempfile.read.return_value = "edited content"

    # Mock the tempfile object to return our mock
    cli.jira._tempfile = mock_tempfile

    # Simulate prompt failure
    with patch(
        "jira_creator.rh_jira.JiraPromptLibrary.get_prompt", side_effect=Exception("💥")
    ):
        cli.edit_issue(args)

    # Check that fallback prompt was used
    assert cli.default_prompt == "fallback prompt"
