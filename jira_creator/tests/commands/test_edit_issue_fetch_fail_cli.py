from unittest.mock import MagicMock


def test_edit_issue_fetch_fail(cli):
    # Mocking the get_description method to raise an exception
    cli.jira.get_description = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-test_edit_issue_fetch_fail"
        no_ai = False

    cli.edit_issue(Args())
