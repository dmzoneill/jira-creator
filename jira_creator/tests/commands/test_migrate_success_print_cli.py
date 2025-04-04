from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_migrate_success_print():
    cli = JiraCLI()

    # Mock the migrate_issue method
    cli.jira.migrate_issue = MagicMock(return_value="AAP-999")
    cli.jira.jira_url = "http://fake"

    # Mock the Args class with necessary attributes
    class Args:
        issue_key = "AAP-123"
        new_type = "story"

    # Call the migrate method
    cli.migrate(Args())
