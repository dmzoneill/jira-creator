from unittest.mock import MagicMock


def test_migrate_success_print(cli):
    # Mock the migrate_issue method
    cli.jira.migrate_issue = MagicMock(return_value="AAP-test_migrate_success_print-0")
    cli.jira.jira_url = "http://fake"

    # Mock the Args class with necessary attributes
    class Args:
        issue_key = "AAP-test_migrate_success_print-1"
        new_type = "story"

    # Call the migrate method
    cli.migrate(Args())
