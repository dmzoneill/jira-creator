from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_set_status_print():
    cli = JiraCLI()

    # Mock the set_status method
    cli.jira.set_status = MagicMock()

    class Args:
        issue_key = "AAP-1"
        status = "Done"

    # Call the method
    cli.set_status(Args())

    # Assert that set_status was called with the correct arguments
    cli.jira.set_status.assert_called_once_with("AAP-1", "Done")
