from unittest.mock import ANY, patch

from jira_creator.rh_jira import JiraCLI


@patch("commands.validate_issue.handle")
def test_validate_issue_delegation(mock_handle):
    cli = JiraCLI()
    fields = {"summary": "Test", "description": "Something"}

    cli.validate_issue(fields)

    mock_handle.assert_called_once_with(fields, ANY)
