from unittest.mock import MagicMock


def test_change_type_failure(cli, capsys):

    # Mocking the change_issue_type method to raise an exception
    cli.jira.change_issue_type = MagicMock(side_effect=Exception("Boom"))

    class Args:
        issue_key = "AAP-1"
        new_type = "task"

    # Call the method
    cli.change_type(Args())

    # Capture the output
    out = capsys.readouterr().out
    assert "❌ Error" in out
    assert "Boom" in out  # Optionally check that the exception message is included
