from unittest.mock import MagicMock


def test_edit_issue_fetch_fail(cli):
    # Mocking the get_description method to raise an exception
    cli.jira.get_description = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-1"
        no_ai = False

    cli.edit_issue(Args())
