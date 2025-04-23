from unittest.mock import MagicMock


def test_set_priority(cli):
    """
    Set the priority for a JIRA ticket using the provided CLI object.

    Arguments:
    - cli (object): The CLI object used to interact with the JIRA system.

    Side Effects:
    - Modifies the 'jira' attribute of the CLI object by assigning it a MagicMock object.
    """

    cli.jira = MagicMock()

    class Args:
        issue_key = "AAP-test_set_priority"
        priority = "High"

    cli.set_priority(Args())

    cli.jira.set_priority.assert_called_once_with("AAP-test_set_priority", "High")
