import pytest
from unittest.mock import MagicMock
from jira_creator.rh_jira import JiraCLI

def test_create_exception(capsys):
    cli = JiraCLI()

    # Mock the ai_provider and create_issue methods
    cli.ai_provider.improve_text = MagicMock(side_effect=lambda p, t: t)
    cli.jira.create_issue = MagicMock(side_effect=Exception("fail"))

    # Mock the TemplateLoader class directly with MagicMock
    class DummyTemplate:
        pass
    
    cli.template_loader = MagicMock(return_value=DummyTemplate())

    # Set up the arguments for the CLI command
    class Args:
        type = "story"
        summary = "Fail"
        edit = False
        dry_run = False

    # Mock input() using MagicMock to simulate user input
    mock_input = MagicMock(return_value="mocked input")
    
    # Mock the input directly on the cli object
    cli.input = mock_input

    # Call the create method and check if the exception is handled
    with pytest.raises(SystemExit):
        cli.create(Args())

    # Check that the expected error message is printed
    out = capsys.readouterr().out
    assert "❌ Failed to create issue" in out
