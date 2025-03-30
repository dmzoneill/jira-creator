from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_add_sprint_exception(capsys):
    cli = JiraCLI()

    # Mock the add_to_sprint_by_name method to raise an exception
    cli.jira.add_to_sprint_by_name = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-1"
        sprint_name = "Sprint X"

    # Call the add_sprint method and handle the exception
    cli.add_sprint(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the expected failure message is present
    assert "❌" in out
