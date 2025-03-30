import sys
import pytest
from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_create_file_not_found():
    cli = JiraCLI()

    # Mock the TemplateLoader to raise FileNotFoundError
    template_loader_mock = MagicMock(side_effect=FileNotFoundError("missing.tmpl"))
    cli.template_loader = template_loader_mock

    # Define the arguments for the CLI command
    class Args:
        type = "nonexistent"
        summary = "test"
        edit = False
        dry_run = False

    # Capture the exit and assert it raises the correct exception
    with pytest.raises(SystemExit):
        cli.create(Args())
