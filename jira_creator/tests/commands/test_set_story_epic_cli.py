from unittest.mock import MagicMock


def test_handle_success(cli, capsys):
    cli.jira.set_story_epic = MagicMock()

    class Args:
        issue_key = "AAP-test_handle_success"
        epic_key = "EPIC-123"

    # Call the handle function
    cli.set_story_epic(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the correct message was printed
    assert "✅ Story's epic set to 'EPIC-123'" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.set_story_epic.assert_called_once_with(
        "AAP-test_handle_success", "EPIC-123"
    )


def test_set_story_epic_exception(cli, capsys):
    cli.jira.set_story_epic = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-test_set_story_epic_exception"
        epic_key = "EPIC-123"

    # Call the handle function
    cli.set_story_epic(Args())

    captured = capsys.readouterr()

    # Assert that the correct error message was printed
    assert "❌ Failed to set epic: fail" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.set_story_epic.assert_called_once_with(
        "AAP-test_set_story_epic_exception", "EPIC-123"
    )
