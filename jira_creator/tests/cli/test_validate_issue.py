from unittest.mock import ANY, MagicMock, patch

from commands import validate_issue

from jira_creator.rh_jira import JiraCLI


@patch("commands.validate_issue.handle")
def test_validate_issue_delegation(mock_handle):
    cli = JiraCLI()
    fields = {"summary": "Test", "description": "Something"}

    cli.validate_issue(fields)

    mock_handle.assert_called_once_with(fields, ANY)


def test_story_without_epic_flagged():
    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = "OK"  # ✅ Mocked correctly

    fields = {
        "issuetype": {"name": "Story"},
        "status": {"name": "To Do"},
        "summary": "Some summary",
        "description": "Some description",
        "customfield_10008": None,  # Epic link missing
        "customfield_12310940": None,
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "customfield_12316543": {"value": "False"},
        "customfield_12316544": "",
        "assignee": {"displayName": "Alice"},
    }

    problems = validate_issue.handle(fields, ai_provider)

    assert "❌ Story has no assigned Epic" in problems
