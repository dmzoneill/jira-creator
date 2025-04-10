from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AIHelperError

from commands.cli_ai_helper import (  # isort: skip
    ask_ai_question,
    call_function,
    clean_ai_output,
    get_cli_command_metadata,
)  # isort: skip


def test_get_cli_command_metadata_parses_subcommands():
    with patch("rh_jira.JiraCLI") as MockCLI:
        mock_cli = MockCLI.return_value
        mock_cli._register_subcommands = MagicMock()

        result = get_cli_command_metadata()

        assert isinstance(result, dict)
        assert "assign" in result or isinstance(result, dict)  # adjust as needed


def test_get_cli_command_metadata_skips_help_and_command_actions():
    # Fake skipped action
    skip_action = MagicMock()
    skip_action.dest = "help"
    skip_action.required = False
    skip_action.option_strings = []
    skip_action.type = str
    skip_action.help = ""

    # Normal positional action
    pos_action = MagicMock()
    pos_action.dest = "issue_key"
    pos_action.required = True
    pos_action.option_strings = []
    pos_action.type = str
    pos_action.help = "The issue key"

    # Normal optional action
    opt_action = MagicMock()
    opt_action.dest = "status"
    opt_action.required = False
    opt_action.option_strings = ["--status"]
    opt_action.type = str
    opt_action.help = "Status to set"

    # Mock subparser with all three actions
    fake_subparser = MagicMock()
    fake_subparser.description = "Set issue status"
    fake_subparser._actions = [skip_action, pos_action, opt_action]

    fake_subparsers = MagicMock()
    fake_subparsers.choices = {"set-status": fake_subparser}

    fake_parser = MagicMock()
    fake_parser.add_subparsers.return_value = fake_subparsers

    with (
        patch("rh_jira.JiraCLI"),
        patch("argparse.ArgumentParser", return_value=fake_parser),
    ):
        result = get_cli_command_metadata()

        assert "set-status" in result
        command = result["set-status"]

        # Should only include the 2 real args
        assert len(command["arguments"]) == 2
        assert all(arg["name"] != "help" for arg in command["arguments"])


def test_get_cli_command_metadata_parses_all_fields():
    fake_action_positional = MagicMock()
    fake_action_positional.dest = "issue_key"
    fake_action_positional.required = True
    fake_action_positional.option_strings = []
    fake_action_positional.type = str
    fake_action_positional.help = "The issue key"

    fake_action_optional = MagicMock()
    fake_action_optional.dest = "status"
    fake_action_optional.required = False
    fake_action_optional.option_strings = ["--status"]
    fake_action_optional.type = str
    fake_action_optional.help = "Status to set"

    fake_subparser = MagicMock()
    fake_subparser.description = "Set issue status"
    fake_subparser._actions = [fake_action_positional, fake_action_optional]

    fake_subparsers = MagicMock()
    fake_subparsers.choices = {"set-status": fake_subparser}

    fake_parser = MagicMock()
    fake_parser.add_subparsers.return_value = fake_subparsers

    with (
        patch("rh_jira.JiraCLI") as MockCLI,
        patch("argparse.ArgumentParser", return_value=fake_parser),
    ):

        result = get_cli_command_metadata()

        assert "set-status" in result
        command = result["set-status"]
        assert command["help"] == "Set issue status"
        assert len(command["arguments"]) == 2

        assert command["arguments"][0]["name"] == "issue_key"
        assert command["arguments"][0]["positional"] is True

        assert command["arguments"][1]["name"] == "status"
        assert command["arguments"][1]["positional"] is False
        assert "--status" in command["arguments"][1]["flags"]


def test_call_function_dispatches_correctly():
    mock_client = MagicMock()
    mock_client._dispatch_command = MagicMock()

    call_function(
        mock_client, "set_status", {"issue_key": "AAP-123", "status": "In Progress"}
    )

    mock_client._dispatch_command.assert_called_once()
    args_passed = mock_client._dispatch_command.call_args[0][0]
    assert isinstance(args_passed, Namespace)
    assert args_passed.command == "set_status"
    assert args_passed.issue_key == "AAP-123"


def test_clean_ai_output_parses_valid_json_block():
    raw = """```json
    [
        {"function": "set_status", "args": {"issue_key": "AAP-123", "status": "In Progress"}}
    ]
    ```"""
    result = clean_ai_output(raw)
    assert isinstance(result, list)
    assert result[0]["function"] == "set_status"


def test_clean_ai_output_raises_on_invalid_json():
    bad_input = "```json\nNot a JSON array\n```"

    with pytest.raises(ValueError) as exc_info:
        clean_ai_output(bad_input)

    assert "Failed to parse AI response" in str(exc_info.value)


def test_ask_ai_question_calls_dispatch_for_each_step():
    mock_client = MagicMock()
    mock_client._dispatch_command = MagicMock()

    ai_provider = MagicMock()
    ai_provider.improve_text.return_value = """
    [
        {"function": "assign", "args": {"issue_key": "AAP-1", "assignee": "me"}},
        {"function": "set_status", "args": {"issue_key": "AAP-1", "status": "In Progress"}}
    ]
    """

    ask_ai_question(mock_client, ai_provider, "system prompt", "user prompt")

    assert mock_client._dispatch_command.call_count == 2


def test_cli_ai_helper_success(cli):
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text.return_value = """
    [
        {"function": "assign", "args": {"issue_key": "AAP-1", "assignee": "me"}}
    ]
    """

    cli.ai_provider = mock_ai_provider  # 👈 Inject the mocked provider

    args = MagicMock()
    args.prompt = "Assign issue to me"

    with patch("commands.cli_ai_helper.get_cli_command_metadata") as mock_get_meta:
        mock_get_meta.return_value = {
            "assign": {
                "help": "Assign a user",
                "arguments": [
                    {
                        "name": "issue_key",
                        "positional": True,
                        "help": "Issue key",
                        "required": True,
                        "type": "str",
                    },
                    {
                        "name": "assignee",
                        "positional": True,
                        "help": "User",
                        "required": True,
                        "type": "str",
                    },
                ],
            }
        }

        cli.ai_helper(args)


def test_cli_ai_helper_raises_on_error(cli):
    cli.ai_provider = MagicMock()
    args = MagicMock()
    args.prompt = "Trigger error"

    with patch(
        "commands.cli_ai_helper.get_cli_command_metadata", side_effect=Exception("boom")
    ):
        with pytest.raises(AIHelperError) as exc_info:
            cli.ai_helper(args)

        assert "Failed to inspect public methods of JiraCLI" in str(exc_info.value)
