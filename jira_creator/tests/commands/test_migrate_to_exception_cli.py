from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_migrate_to_exception(capsys):
    cli = JiraCLI()

    # Mock the migrate_issue method to raise an exception
    cli.jira.migrate_issue = MagicMock(side_effect=Exception("fail"))
    cli.jira.jira_url = "http://fake"

    # Mock the Args class with necessary attributes
    class Args:
        issue_key = "AAP-123"
        new_type = "story"

    # Call the migrate method
    cli.migrate(Args())

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Migration failed" in out
