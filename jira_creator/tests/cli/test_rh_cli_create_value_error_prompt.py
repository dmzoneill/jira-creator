import pytest
from unittest.mock import MagicMock, patch
from jira_creator.rh_jira import JiraCLI
from jira_creator.jira import jira_prompts


def test_create_value_error_prompt():
    cli = JiraCLI()

    # Mock create_issue to return a fake issue key
    cli.jira.create_issue = MagicMock(return_value="AAP-123")

    # Mock the improve_text method to return the text unchanged
    cli.ai_provider.improve_text = MagicMock(side_effect=lambda p, t: t)

    # Mock TemplateLoader to return a DummyTemplate instance
    class DummyTemplate:
        pass

    cli.jira.TemplateLoader = MagicMock(return_value=DummyTemplate())

    # Simulate unknown issue type causing ValueError in the JiraIssueType method
    jira_prompts.JiraIssueType = MagicMock(side_effect=ValueError("unknown type"))

    # Create a dummy Args class to simulate the input
    class Args:
        type = "unknown"
        summary = "Some summary"
        edit = False
        dry_run = True

    # Catch the SystemExit triggered by sys.exit(1) when FileNotFoundError occurs
    with pytest.raises(SystemExit) as excinfo:
        cli.create(Args())

    # Assert that sys.exit(1) was called
    assert excinfo.value.code == 1
