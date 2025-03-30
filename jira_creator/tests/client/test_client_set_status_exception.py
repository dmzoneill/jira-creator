from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_set_status_exception(capsys):
    cli = JiraCLI()

    # Mock the set_status method to simulate an exception
    cli.jira.set_status = MagicMock(side_effect=Exception("bad status"))

    class Args:
        issue_key = "AAP-900"
        status = "Invalid"

    # Call the method
    cli.set_status(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to update status" in out
