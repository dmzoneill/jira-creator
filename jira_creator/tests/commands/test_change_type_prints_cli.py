from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_change_type_prints(capsys):
    cli = JiraCLI()

    # Mocking the change_issue_type method
    cli.jira.change_issue_type = MagicMock(return_value=True)

    class Args:
        issue_key = "AAP-123"
        new_type = "story"

    # Call the method
    cli.change_type(Args())

    # Capture the output
    out = capsys.readouterr().out
    # Correct the expected output to match the actual printed output
    assert "✅ Changed AAP-123 to 'story'" in out
