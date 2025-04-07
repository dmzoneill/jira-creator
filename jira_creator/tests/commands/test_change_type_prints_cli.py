from unittest.mock import MagicMock


def test_change_type_prints(cli, capsys):
    # Mocking the change_issue_type method
    cli.jira.change_issue_type = MagicMock(return_value=True)

    class Args:
        issue_key = "AAP-test_change_type_prints"
        new_type = "story"

    # Call the method
    cli.change_type(Args())

    # Capture the output
    out = capsys.readouterr().out
    # Correct the expected output to match the actual printed output
    assert "✅ Changed AAP-test_change_type_prints to 'story'" in out
