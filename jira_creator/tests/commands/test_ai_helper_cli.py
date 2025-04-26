#!/usr/bin/env python
"""
This module contains unit tests for the AI helper command line interface (CLI) functionality.
The tests cover various aspects of the CLI AI helper, including command dispatching, error handling, and output
processing.

Key functions tested:
- `call_function`: Verifies correct command dispatching.
- `ask_ai_question`: Tests various scenarios including error handling, valid responses, and invalid JSON.
- `clean_ai_output`: Ensures proper parsing of AI output.
- `get_cli_command_metadata`: Validates the correct parsing of command metadata for CLI commands.

The tests utilize the `pytest` framework and include mocking of dependencies to isolate functionality and control test
scenarios.
"""

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
    """
    Simulates a test scenario for calling a function.

    Arguments:
    No arguments.

    Returns:
    No return value.
    """

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
    """
    Execute a test for an AI helper function using the provided command line interface (CLI).

    Arguments:
    - cli (object): The command line interface object used for testing.

    Exceptions:
    - Raises an Exception using pytest if an error occurs during the test execution.
    """

    with pytest.raises(Exception):

        class Args:
            voice: bool

        cli.ai_helper(Args())


def test_get_cli_command_metadata_parses_correctly(cli):
    """
    Parses CLI command metadata for a specific CLI.

    Arguments:
    - cli (object): The Command Line Interface (CLI) object to parse metadata for.
    """

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


def test_get_cli_command_metadata_skip_help_and_command():
    """
    Test to ensure that the 'continue' statement correctly skips actions with 'help' or 'command' in their 'dest'.

    Arguments:
    No arguments.

    Returns:
    No return value.

    Exceptions:
    No exceptions raised.
    """

    # Create fake actions with the 'dest' values "help" and "command" that should be skipped
    fake_action_help = MagicMock()
    fake_action_help.dest = "help"

    fake_action_command = MagicMock()
    fake_action_command.dest = "command"

    fake_action_other = MagicMock()
    fake_action_other.dest = "other"

    # Mock type to include __name__ attribute for the actions
    fake_action_help.type = MagicMock()
    fake_action_help.type.__name__ = "str"

    fake_action_command.type = MagicMock()
    fake_action_command.type.__name__ = "str"

    fake_action_other.type = MagicMock()
    fake_action_other.type.__name__ = "str"

    # Create a fake subparser and assign actions to it
    fake_subparser = MagicMock()
    fake_subparser._actions = [fake_action_help, fake_action_command, fake_action_other]
    fake_subparser.description = "Test Command"

    # Mock subparsers and their choices
    fake_subparsers = MagicMock()
    fake_subparsers.choices = {"test-command": fake_subparser}

    # Mock the ArgumentParser
    fake_parser = MagicMock()
    fake_parser.add_subparsers.return_value = fake_subparsers

    # Use patch to mock the ArgumentParser in the get_cli_command_metadata function
    with patch("argparse.ArgumentParser", return_value=fake_parser):
        result = get_cli_command_metadata()

    # Check that "test-command" was added to the result
    assert "test-command" in result
    command = result["test-command"]

    # Verify that the "help" and "command" actions are not in the command arguments
    assert not any(arg["name"] == "help" for arg in command["arguments"])
    assert not any(arg["name"] == "command" for arg in command["arguments"])

    # Check that the "other" action is included
    assert any(arg["name"] == "other" for arg in command["arguments"])


@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_returns_true(mock_os_system, mock_gtts):
    """
    Test the last return statement in the ask_ai_question function,
    ensuring that the function returns True when ai_generated_steps is a non-empty list.
    """

    # Create a mock for the ai_provider
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text.return_value = None

    # Mock the clean_ai_output function to return a parsed list (as if AI generated steps)
    with patch("commands.cli_ai_helper.clean_ai_output", return_value=None):
        # Create a mock CLI object
        mock_cli = MagicMock()

        # Call the function with the required parameters
        result = ask_ai_question(
            mock_cli, mock_ai_provider, "System prompt", "User prompt", voice=False
        )

        # Check that the function returned True
        assert result is True


def test_clean_ai_output(cli):
    """
    Clean the output of an AI tool by parsing and converting it into a list of dictionaries.

    Arguments:
    - raw_valid (str): A string containing JSON-formatted data outputted by an AI tool.

    Return:
    - list: A list of dictionaries representing the parsed data extracted from the input string.

    Exceptions:
    - None
    """

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
    assert "Expecting value: line 1" in str(exc_info.value)


# Test Case: cli_ai_helper - Verifies that AIHelperError is raised when get_cli_command_metadata throws an exception
def test_cli_ai_helper_exception(cli):
    """
    Simulate an exception scenario in the CLI AI helper.

    Arguments:
    - cli: An instance of the CLI to be tested.

    Exceptions:
    - AIHelperError: Raised when there is an error fetching metadata.

    Side Effects:
    - Modifies the behavior of 'get_cli_command_metadata' to raise an exception.

    The function tests the CLI AI helper by mocking the 'get_cli_command_metadata' function to raise an 'AIHelperError'
    exception. It then asserts that the exception is raised when the function is called with the provided mocks.
    """

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
            assert "Metadata fetching error" in str(exc_info.value)

            # Verify that ask_ai_question was not called because of the exception
            mock_ask_ai_question.assert_not_called()


# Test Case 1: AI generates an error message (returns a dictionary with "error" key)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_error(mock_os_system, mock_gtts):
    """
    Simulate asking an AI question and handle error response.

    Arguments:
    - mock_os_system: A MagicMock object mocking the os.system function.
    - mock_gtts: A MagicMock object mocking the Google Text-to-Speech function.

    Exceptions:
    None
    """

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
    """
    Simulates asking an AI system a question without errors.

    Arguments:
    - mock_os_system: MagicMock object for mocking the OS system.
    - mock_gtts: MagicMock object for mocking the Google Text-to-Speech service.
    """

    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(
        return_value='{"info": "Some steps to take"}'
    )

    result = ask_ai_question(
        mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
    )

    assert result is False
    mock_gtts.assert_not_called()  # No TTS should be triggered


# Test Case 3: AI generates a list of steps (returns a list of dictionaries)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
@patch(
    "commands.cli_ai_helper.call_function"
)  # Mock the call_function to avoid calling real functions
def test_ask_ai_question_steps(mock_call_function, mock_os_system, mock_gtts):
    """
    Simulates the steps for asking an AI question in a test environment.

    Arguments:
    - mock_call_function: A MagicMock object representing a function call.
    - mock_os_system: A MagicMock object representing an OS system call.
    - mock_gtts: A MagicMock object representing Google Text-to-Speech.

    No return value.

    Side Effects:
    - Initializes mock_client as a MagicMock object.
    - Initializes mock_ai_provider as a MagicMock object with the improve_text method returning a specific JSON string.
    """

    mock_client = MagicMock()
    mock_ai_provider = MagicMock()
    mock_ai_provider.improve_text = MagicMock(
        return_value='[{"function": "function1", "args": {"arg1": "value1"}, "action": "test"}]'
    )

    result = ask_ai_question(
        mock_client, mock_ai_provider, "system prompt", "user prompt", voice=True
    )

    assert result is True
    mock_call_function.assert_called_once_with(
        mock_client, "function1", {"arg1": "value1"}
    )
    mock_os_system.assert_called_once_with("mpg123 output.mp3")


# Test Case 4: AI generates an empty list (returns an empty list)
@patch("commands.cli_ai_helper.gTTS")  # Mock gTTS to avoid audio generation
@patch("commands.cli_ai_helper.os.system")  # Mock os.system to prevent external calls
def test_ask_ai_question_empty_steps(mock_os_system, mock_gtts):
    """
    Simulate asking an AI question with empty steps.

    Arguments:
    - mock_os_system: A MagicMock object representing the mocked os.system function.
    - mock_gtts: A MagicMock object representing the mocked gtts library.
    """

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
    """
    Simulates asking an AI question with invalid JSON input.

    Arguments:
    - mock_os_system: MagicMock object for mocking the os.system function.
    - mock_gtts: MagicMock object for mocking the Google Text-to-Speech function.

    Side Effects:
    - Creates a MagicMock object for client simulation.
    - Creates a MagicMock object for AI provider simulation with a method to improve text.
    """

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
    """
    Simulate a successful test scenario for a CLI AI helper function.

    Arguments:
    - mock_ask_ai_question: A mock object for asking AI questions.
    - mock_get_cli_command_metadata: A mock object for retrieving CLI command metadata.
    - cli: The CLI object used for testing.

    Side Effects:
    - Sets up mock return values for the dependencies to simulate a successful test scenario.
    """

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
