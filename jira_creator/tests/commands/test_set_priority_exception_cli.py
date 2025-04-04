from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_set_priority_error(capsys):
    cli = JiraCLI()

    # Mock the set_priority method to simulate an exception
    cli.jira.set_priority = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-4"
        priority = "High"

    # Call the method
    cli.set_priority(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to set priority" in out
