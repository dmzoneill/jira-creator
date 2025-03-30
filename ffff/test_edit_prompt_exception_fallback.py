from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_edit_prompt_exception_fallback():
    cli = JiraCLI()

    # Mock JiraClient methods
    cli.jira.get_description = MagicMock(return_value="desc")
    cli.jira.get_issue_type = MagicMock(
        side_effect=Exception("fail")
    )  # Mock to raise exception
    cli.jira.update_description = MagicMock(
        return_value=None
    )  # Mock update_description

    # Mock AI provider
    cli.ai_provider.improve_text = MagicMock(return_value="desc")

    # Create a dummy temporary file class
    class DummyTempFile:
        def __init__(self):
            self.name = "temp.md"

    # Patch the tempfile.NamedTemporaryFile method
    cli.jira._tempfile = DummyTempFile

    # Create Args object and run the edit_issue method
    class Args:
        issue_key = "AAP-1"
        no_ai = False

    # Ensure the exception does not prevent the flow
    try:
        cli.edit_issue(Args())
    except Exception:
        pass  # Ensure the exception doesn't stop the test

    # Assertions
    cli.jira.update_description.assert_called_once()  # Check if update_description was called
