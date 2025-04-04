from unittest.mock import MagicMock, patch

from jira_creator.rh_jira import JiraCLI


def test_handle_success(capsys):
    cli = JiraCLI()
    cli.jira.set_story_epic = MagicMock()

    class Args:
        issue_key = "AAP-1"
        epic_key = "EPIC-123"

    # Call the handle function
    cli.set_story_epic(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the correct message was printed
    assert "✅ Story's epic set to 'EPIC-123'" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.set_story_epic.assert_called_once_with("AAP-1", "EPIC-123")


def test_set_story_epic_exception(capsys):
    cli = JiraCLI()
    cli.jira.set_story_epic = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-1"
        epic_key = "EPIC-123"

    # Call the handle function
    cli.set_story_epic(Args())

    captured = capsys.readouterr()

    # Assert that the correct error message was printed
    assert "❌ Failed to set epic: fail" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.set_story_epic.assert_called_once_with("AAP-1", "EPIC-123")
