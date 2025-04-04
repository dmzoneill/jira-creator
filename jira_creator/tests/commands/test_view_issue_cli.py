from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_view_issue(capsys):

    blob = {"smokekey": "somevalue", "customfield": 3}

    cli = JiraCLI()
    cli.jira.get_field_name = MagicMock(return_value="xxx")
    cli.jira.view_issue = MagicMock(return_value=blob)

    class Args:
        issue_key = "AAP-1"

    # Call the handle function
    cli.view_issue(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the correct message was printed
    # assert "✅ Story's epic set to 'EPIC-123'" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-1")


def test_view_issue_exception(capsys):
    cli = JiraCLI()
    cli.jira.view_issue = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-1"

    # Call the handle function
    cli.view_issue(Args())

    captured = capsys.readouterr()

    # Assert that the correct error message was printed
    assert "❌ Unable to view issue: fail" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-1")
