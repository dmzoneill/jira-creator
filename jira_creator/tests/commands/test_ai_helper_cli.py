from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AIHelperError

from commands.cli_ai_helper import (  # isort: skip
    ask_ai_question,
    clean_ai_output,
    get_cli_command_metadata,
    call_function,
)  # isort: skip


# Test Case: call_function - Verifies that the function dispatches the correct command
def test_call_function():
    # Mock the client and its _dispatch_command method
    mock_client = MagicMock()
    mock_client._dispatch_command = MagicMock()

    # Define the function name and arguments
    function_name = "test_command"
    args_dict = {"arg1": "value1", "arg2": "value2"}

    # Call the function
    call_function(mock_client, function_name, args_dict)

    # Create expected Namespace
    expected_args = Namespace(**args_dict)
    setattr(expected_args, "command", function_name)  # Required for _dispatch_command

    # Check that _dispatch_command was called with the correct args
    mock_client._dispatch_command.assert_called_once_with(expected_args)


def test_ai_helper_exec(cli):
    with pytest.raises(Exception):

        class Args:
            voice: bool

        cli.ai_helper(Args())


def test_get_cli_command_metadata_parses_correctly(cli):
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

    # Mocking subcommands with a mix of actions
    fake_subparser = MagicMock()
    fake_subparser.description = "Set issue status"
    fake_subparser._actions = [fake_action_positional, fake_action_optional]

    fake_subparsers = MagicMock()
    fake_subparsers.choices = {"set-status": fake_subparser}

    fake_parser = MagicMock()
    fake_parser.add_subparsers.return_value = fake_subparsers

    with patch("argparse.ArgumentParser", return_value=fake_parser):
        result = get_cli_command_metadata()

        assert "set-status" in result
        command = result["set-status"]

        # Assertions common to all tests
        assert command["help"] == "Set issue status"

        # Checking that only real arguments are included
        assert all(arg["name"] != "help" for arg in command["arguments"])
        assert command["arguments"][0]["name"] == "issue_key"
        assert command["arguments"][0]["positional"] is True

        assert command["arguments"][1]["name"] == "status"
        assert command["arguments"][1]["positional"] is False
        assert "--status" in command["arguments"][1]["flags"]


def test_clean_ai_output(cli):
    # Test valid JSON
    raw_valid = """```json
    [
        {"function": "set_status", "args": {"issue_key": "AAP-123", "status": "In Progress"}, "action": "test"}
    ]
    ```"""
    result = clean_ai_output(raw_valid)
    assert isinstance(result, list)
    assert result[0]["function"] == "set_status"

    # Test invalid JSON
    raw_invalid = "```json\nNot a JSON array\n```"
    with pytest.raises(ValueError) as exc_info:
        clean_ai_output(raw_invalid)
    assert "Failed to parse AI response" in str(exc_info.value)


# Test Case: cli_ai_helper - Verifies that AIHelperError is raised when get_cli_command_metadata throws an exception
def test_cli_ai_helper_exception(cli):
    # Mock get_cli_command_metadata to raise an exception
    with patch(
        "commands.cli_ai_helper.get_cli_command_metadata",
        side_effect=AIHelperError("Metadata fetching error"),
    ):
        with patch("commands.cli_ai_helper.ask_ai_question") as mock_ask_ai_question:
            with pytest.raises(AIHelperError) as exc_info:
                # Call the function with the mocks
                class Args:
                    voice: False
                    prompt: str

                args = Args()
                args.prompt = "Do something with issue"

                cli.ai_helper(args)

            # Check if AIHelperError was raised with the correct message
            assert "Failed to inspect public methods of JiraCLI" in str(exc_info.value)
            assert "Metadata fetching error" in str(exc_info.value)

            # Verify that ask_ai_question was not called because of the exception
            mock_ask_ai_question.assert_not_called()


# Test Case 1: AI generates an error message (returns a dictionary with "error" key)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_error(mock_os_system, mock_gtts):
    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(
        return_value='{"error": "Something went wrong"}'
    )

    result = ask_ai_question(
        mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
    )

    assert result is False
    mock_os_system.assert_called_once_with("mpg123 output.mp3")
    mock_gtts.assert_called_once_with(text="Something went wrong", lang="en")


# Test Case 2: AI generates a non-error response (returns a dictionary without "error")
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_no_error(mock_os_system, mock_gtts):
    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(
        return_value='{"info": "Some steps to take"}'
    )

    result = ask_ai_question(
        mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
    )

    assert result is None
    mock_gtts.assert_not_called()  # No TTS should be triggered


# Test Case 3: AI generates a list of steps (returns a list of dictionaries)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
@patch(
    "commands.cli_ai_helper.call_function"
)  # Mock the call_function to avoid calling real functions
def test_ask_ai_question_steps(mock_call_function, mock_os_system, mock_gtts):
    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(
        return_value='[{"function": "function1", "args": {"arg1": "value1"}, "action": "test"}]'
    )

    result = ask_ai_question(
        mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
    )

    assert result is None
    mock_call_function.assert_called_once_with(
        mock_client, "function1", {"arg1": "value1"}
    )
    mock_os_system.assert_called_once_with("mpg123 output.mp3")


# Test Case 4: AI generates an empty list (returns an empty list)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_empty_steps(mock_os_system, mock_gtts):
    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(return_value="[]")

    result = ask_ai_question(
        mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
    )

    assert result is False
    mock_gtts.assert_not_called()  # No TTS should be triggered


# Test Case 5: AI generates an invalid JSON (raises ValueError)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_invalid_json(mock_os_system, mock_gtts):
    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(return_value="Invalid JSON")

    with pytest.raises(ValueError):
        ask_ai_question(
            mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
        )


# Test Case: Verifies that cli_ai_helper returns True when everything works correctly


@patch(
    "commands.cli_ai_helper.get_cli_command_metadata"
)  # Mock get_cli_command_metadata to return fake data
@patch(
    "commands.cli_ai_helper.ask_ai_question"
)  # Mock ask_ai_question to avoid actual AI processing
def test_cli_ai_helper_success(
    mock_ask_ai_question, mock_get_cli_command_metadata, cli
):
    # Setup mock return values for the dependencies
    mock_get_cli_command_metadata.return_value = {
        "command1": {
            "arguments": [{"name": "arg1", "positional": True, "help": "Help for arg1"}]
        },
        "command2": {
            "arguments": [
                {"name": "arg2", "positional": False, "help": "Help for arg2"}
            ]
        },
    }

    mock_args = MagicMock()  # Mock args
    mock_args.prompt = "Test prompt"
    mock_args.voice = True

    # Call the function
    result = cli.ai_helper(mock_args)

    # Verify that get_cli_command_metadata and ask_ai_question were called
    mock_get_cli_command_metadata.assert_called_once()
    mock_ask_ai_question.assert_called_once()

    # Check if the function returns True
    assert result is True
