import pytest
from exceptions.exceptions import FetchDescriptionError


def test_edit_issue_fetch_fail(cli):
    # Mocking the get_description method to raise an exception
    cli.jira.get_description.side_effect = FetchDescriptionError("fail")

    class Args:
        issue_key = "AAP-test_edit_issue_fetch_fail"
        no_ai = False

    with pytest.raises(FetchDescriptionError):
        cli.edit_issue(Args())
