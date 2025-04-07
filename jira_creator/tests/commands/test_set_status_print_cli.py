from unittest.mock import MagicMock


def test_set_status_print(cli):
    # Mock the set_status method
    cli.jira.set_status = MagicMock()

    class Args:
        issue_key = "AAP-test_set_status_print"
        status = "Done"

    # Call the method
    cli.set_status(Args())

    # Assert that set_status was called with the correct arguments
    cli.jira.set_status.assert_called_once_with("AAP-test_set_status_print", "Done")
