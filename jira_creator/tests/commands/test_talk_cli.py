#!/usr/bin/env python
"""
This module contains unit tests for the `cli_talk` command-line interface, focusing on audio processing, text
communication, and utility functions.

The tests are organized to validate the functionality of various methods, including `flush_queue`,
`fuzzy_digit_cleanup`, `word_digits_to_numbers`, `combine_consecutive_digits`, `normalize_issue_references`,
`initialize_recognizer`, `process_audio_data`, and `process_text_and_communicate`. Each test case utilizes the `pytest`
framework and incorporates mock objects to simulate dependencies, ensuring that functions respond correctly to both
expected inputs and edge cases.

Key functions tested include:
- `test_flush_queue_empty_exception`: Tests exception handling for an empty queue in `flush_queue`.
- `test_do_once`: Verifies the return value of the `do_once` function.
- `test_cli_exec`: Tests execution of the CLI talk function.
- `test_fuzzy_digit_cleanup`: Validates the fuzzy digit cleanup functionality.
- `test_word_digits_to_numbers`: Checks conversion of word digits to numerical representation.
- `test_combine_consecutive_digits`: Ensures consecutive digits are combined correctly.
- `test_normalize_issue_references`: Tests normalization of issue references in text.
- `test_flush_queue`: Verifies the flushing of the queue.
- `test_suppress_stderr`: Tests suppression of standard error output.
- `test_initialize_recognizer`: Ensures correct initialization of the recognizer.
- `test_process_text_and_communicate`: Tests processing of text and communication with AI.
- `test_process_audio_data`: Validates audio data processing for various scenarios.
- `test_cli_talk`: Tests the main CLI talk function with different audio inputs.

The module also includes a fixture, `cli_talk_mocks`, which sets up mock objects for testing CLI talk functionality,
allowing for controlled testing of the command line interactions and audio processing logic.
"""

import queue
import sys
from unittest.mock import MagicMock, patch

import pytest

from commands.cli_talk import (  # isort: skip
    combine_consecutive_digits,
    callback,
    cli_talk,
    do_once,
    flush_queue,
    fuzzy_digit_cleanup,
    initialize_recognizer,
    normalize_issue_references,
    process_audio_data,
    process_text_and_communicate,
    suppress_stderr,
    word_digits_to_numbers,
)  # isort: skip


# Test Case: flush_queue - Verifies that the function handles queue.Empty exception
def test_flush_queue_empty_exception():
    """
    Simulate a test scenario to ensure an exception is raised when trying to flush an empty queue.

    Arguments:
    No arguments.

    Exceptions:
    No exceptions raised explicitly in this function.
    """

    # Create a mock queue and put some items in it
    q = queue.Queue()
    q.put("item1")
    q.put("item2")

    # Now, simulate the queue being empty
    q.get_nowait = MagicMock(side_effect=queue.Empty)

    # Call flush_queue and ensure that it handles the exception correctly
    flush_queue(q)

    # Verify that the queue is now empty (after trying to get items)
    assert q.empty() is False

    # Check that get_nowait was called twice (for both items)
    q.get_nowait.assert_called_with()


def test_do_once():
    """
    This function tests the behavior of the 'do_once' function by asserting that its return value is False.
    """

    assert do_once() is False


def test_cli_exec(cli, cli_talk_mocks):
    """
    Execute a test for a command line interface function.

    Arguments:
    - cli: The command line interface function to be tested.
    - cli_talk_mocks: Mock objects for simulating CLI interaction.

    Side Effects:
    - Defines a class Args with attributes prompt (str) and voice (bool).
    """

    class Args:
        prompt: str
        voice: bool

    cli.talk(Args())


# Test Case 1: fuzzy_digit_cleanup
def test_fuzzy_digit_cleanup():
    """
    This function performs fuzzy digit cleanup by replacing fuzzy number words with their corresponding numerical
    digits.

    Arguments:
    - text (str): A string containing text with fuzzy number words.

    Return:
    - str: The input text with fuzzy number words replaced by their numerical digits.
    """

    assert fuzzy_digit_cleanup("I have forty apples") == "I have four apples"
    assert fuzzy_digit_cleanup("I have tirty oranges") == "I have three oranges"
    assert fuzzy_digit_cleanup("I see a tree") == "I see a three"
    assert fuzzy_digit_cleanup("My phone number is won") == "My phone number is one"
    assert fuzzy_digit_cleanup("I ate twenty cookies") == "I eight two cookies"


# Test Case 2: word_digits_to_numbers
def test_word_digits_to_numbers():
    """
    Converts word representations of numbers to actual numerical digits in a given sentence.

    Arguments:
    - sentence (str): A string containing words representing numbers.

    Return:
    - str: The input sentence with word numbers converted to numerical digits.
    """

    assert word_digits_to_numbers("I have four apples") == "I have 4 apples"
    assert word_digits_to_numbers("I have three oranges") == "I have 3 oranges"
    assert word_digits_to_numbers("I see five trees") == "I see 5 trees"
    assert (
        word_digits_to_numbers("My address is nine street") == "My address is 9 street"
    )


# Test Case 3: combine_consecutive_digits
def test_combine_consecutive_digits():
    """
    Combine consecutive digits in a string by removing spaces between them.

    Arguments:
    - s (str): A string containing digits separated by spaces.

    Return:
    - str: A new string where consecutive digits are combined without spaces.
    """

    assert combine_consecutive_digits("4 3 2 1") == "4321"
    assert combine_consecutive_digits("7 5") == "75"
    assert combine_consecutive_digits("1 2 3") == "123"
    assert combine_consecutive_digits("I have 1 0 0 0 dollars") == "I have 1000 dollars"


# Test Case 4: normalize_issue_references
def test_normalize_issue_references():
    """
    Normalize the issue references in a given text.

    Arguments:
    - text (str): The input text that may contain references to issues.

    Return:
    - str: The input text with normalized issue references.
    """

    assert normalize_issue_references("No issues found here") == "No issues found here"

    # Testing case where "issue" is followed by digits
    assert (
        normalize_issue_references("This is issue one two three") == "This is XYZ-123"
    )

    # Testing a single issue with a fuzzy word conversion
    assert normalize_issue_references("This is issue fife") == "This is XYZ-5"

    # Testing multiple issues in the same string
    assert normalize_issue_references("issue three issue twenty") == "XYZ-3 XYZ-2"

    # Testing mixed word references to ensure both 'issue' and non-'issue' tokens are processed
    assert (
        normalize_issue_references("issue tree and issue twenty") == "XYZ-3 and XYZ-2"
    )

    # Testing string without any 'issue' to ensure else branch is hit
    assert normalize_issue_references("This is a test") == "This is a test"

    # Adding a more complex example where 'issue' is followed by digits and other words
    assert (
        normalize_issue_references("issue five and issue twenty") == "XYZ-5 and XYZ-2"
    )

    # No issue number after issue
    assert normalize_issue_references("issue and") == "issue and"


# Test Case 6: flush_queue
def test_flush_queue():
    """
    Flushes all items from the queue.

    Arguments:
    No arguments.
    """

    q = queue.Queue()
    q.put("item1")
    q.put("item2")

    flush_queue(q)

    assert q.empty()


# Test Case 8: suppress_stderr
def test_suppress_stderr():
    """
    Suppresses the standard error output temporarily within a context.

    This function is used as a context manager to suppress any output that would normally be printed to the standard
    error stream (sys.stderr) within the context block.

    Arguments:
    No arguments are passed explicitly to this function.

    Side Effects:
    Temporarily suppresses the standard error output within the context block.
    """

    with suppress_stderr():
        print("This should not be printed", file=sys.stderr)

    assert True


# Test Case: initialize_recognizer - Verifies that the recognizer is initialized correctly
@patch("commands.cli_talk.Model")
@patch("commands.cli_talk.KaldiRecognizer")
def test_initialize_recognizer(MockKaldiRecognizer, MockModel):
    """
    Initialize a recognizer for testing purposes using mock objects.

    Arguments:
    - MockKaldiRecognizer: A mock object representing a Kaldi recognizer.
    - MockModel: A mock object representing a model.

    Side Effects:
    - Initializes mock objects for model and recognizer for testing.
    """

    # Setup mocks
    mock_model = MagicMock()
    mock_recognizer = MagicMock()

    MockModel.return_value = mock_model
    MockKaldiRecognizer.return_value = mock_recognizer

    # Call the function
    rec = initialize_recognizer()

    # Verify that Model and KaldiRecognizer were called with the correct arguments
    MockModel.assert_called_once()
    MockKaldiRecognizer.assert_called_once_with(mock_model, 16000)

    # Verify the returned object is the recognizer
    assert rec == mock_recognizer


# Test Case: process_text_and_communicate - Verifies that the text is processed and AI helper is called
def test_process_text_and_communicate_normal_case(cli):
    """
    Processes the given text input for AI completion and communicates the result via CLI.

    Arguments:
    - cli (bool): A boolean flag indicating whether to communicate the result via CLI.
    - text (str): The text input to be processed by the AI for completion.
    - voice (bool): A boolean flag indicating whether the input text includes voice data.

    Side Effects:
    - Communicates the processed text result via the Command Line Interface (CLI).
    """

    text = "Test input for AI to complete alot"
    voice = True

    cli.ai_provider.improve_text = MagicMock()
    cli.ai_provider.improve_text.return_value = "```json {}```"

    # Call the function
    result = process_text_and_communicate(text, cli, voice)

    # Ensure ai_helper is called with the correct arguments
    class Args:
        prompt: str
        voice: bool

    args = Args()
    args.prompt = text
    args.voice = True

    cli.ai_provider.improve_text.assert_called()

    # Assert that the function returns False (no 'stop' in the text)
    assert not result


def test_process_text_and_communicate_stop(cli):
    """
    Processes the given text and communicates the stop command via the provided command line interface.

    Arguments:
    - cli (CommandLineInterface): The command line interface used to communicate the stop command.

    Side Effects:
    - Modifies the global variables 'text' and 'voice'.
    """

    text = "Stop"
    voice = True

    # Call the function
    result = process_text_and_communicate(text, cli, voice)

    # Ensure ai_helper is not called (as the text is 'stop')
    cli.ai_provider.improve_text.assert_not_called()

    # Assert that the function returns True (ends when 'stop' is in the text)
    assert result


def test_process_text_and_communicate_too_few_words(cli):
    """
    Processes the given text and communicates it using a specified method.

    Arguments:
    - cli (str): The method used for communication.

    Side Effects:
    - Modifies the 'text' and 'voice' variables.
    """

    text = "Too few words"
    voice = True

    result = process_text_and_communicate(text, cli, voice)

    # Assert that the function returns False (as there are not enough words)
    assert not result


# Test Case: process_audio_data - Verifies correct audio data processing


@patch("json.loads")
def test_process_audio_data_valid(mock_json_loads):
    """
    Process valid audio data using mocked JSON loads function.

    Arguments:
    - mock_json_loads: A MagicMock object representing the mocked JSON loads function.

    Side Effects:
    - Creates a MagicMock object 'mock_q'.
    - Creates a MagicMock object 'mock_rec'.

    The function processes audio data by simulating valid audio data retrieval, acceptance, and recognition using
    mocked objects. It then uses the mocked JSON loads function to process the recognized text. The result is the
    recognized text extracted from the audio data.
    """

    # Setup
    mock_q = MagicMock()
    mock_rec = MagicMock()

    # Simulate valid audio data and mock json.loads
    mock_q.get.return_value = b"valid audio data"
    mock_rec.AcceptWaveform.return_value = True
    mock_json_loads.return_value = {"text": "Recognized Text"}

    # Call the function
    result = process_audio_data(mock_q, mock_rec)

    # Assert the result is the recognized text
    assert result == "Recognized Text"

    # Ensure get and AcceptWaveform were called
    mock_q.get.assert_called_once()
    mock_rec.AcceptWaveform.assert_called_once_with(b"valid audio data")
    mock_json_loads.assert_called_once_with(mock_rec.Result())


@patch("json.loads")
def test_process_audio_data_invalid(mock_json_loads):
    """
    Processes audio data from a JSON file and performs validation.

    Arguments:
    - mock_json_loads: A MagicMock object for the json.loads function.

    Side Effects:
    - Creates a MagicMock object for the q variable.
    - Creates a MagicMock object for the rec variable.
    """

    # Setup
    mock_q = MagicMock()
    mock_rec = MagicMock()

    # Simulate invalid audio data
    mock_q.get.return_value = b"invalid audio data"
    mock_rec.AcceptWaveform.return_value = False

    # Call the function
    result = process_audio_data(mock_q, mock_rec)

    # Assert that the result is None due to invalid data
    assert result is None

    # Ensure get and AcceptWaveform were called
    mock_q.get.assert_called_once()
    mock_rec.AcceptWaveform.assert_called_once_with(b"invalid audio data")
    mock_json_loads.assert_not_called()


@patch("json.loads")
def test_process_audio_data_empty_result(mock_json_loads):
    """
    Processes audio data and handles empty results.

    Arguments:
    - mock_json_loads: A mock object for JSON deserialization.

    Side Effects:
    - Uses MagicMock objects mock_q and mock_rec for testing purposes.
    """

    # Setup
    mock_q = MagicMock()
    mock_rec = MagicMock()

    # Simulate audio data being accepted
    mock_q.get.return_value = b"valid audio data"
    mock_rec.AcceptWaveform.return_value = True

    # Simulate the result being empty
    mock_json_loads.return_value = {"text": ""}

    # Call the function
    result = process_audio_data(mock_q, mock_rec)

    # Assert that the result is None because the text is empty
    assert result is None

    # Ensure get and AcceptWaveform were called
    mock_q.get.assert_called_once()
    mock_rec.AcceptWaveform.assert_called_once_with(b"valid audio data")
    mock_json_loads.assert_called_once_with(mock_rec.Result())


@pytest.fixture
def cli_talk_mocks():
    """
    Mocks external dependencies for the CLI talk functionality.

    Arguments:
    No arguments.

    Side Effects:
    - Mocks the 'flush_queue', 'process_audio_data', 'process_text_and_communicate', 'RawInputStream', 'do_once',
    'initialize_recognizer', and 'EnvFetcher.get' functions.
    - Sets return values for 'get' and 'initialize_recognizer' functions.
    - Mocks the context manager of the 'RawInputStream' stream.
    """

    with (
        patch("commands.cli_talk.flush_queue") as mock_flush_queue,
        patch("commands.cli_talk.process_audio_data") as mock_process_audio_data,
        patch(
            "commands.cli_talk.process_text_and_communicate"
        ) as mock_process_text_and_communicate,
        patch("commands.cli_talk.sounddevice.RawInputStream") as mock_raw_input_stream,
        patch("commands.cli_talk.do_once") as mock_do_once,
        patch("commands.cli_talk.initialize_recognizer") as mock_initialize_recognizer,
        patch("commands.cli_talk.EnvFetcher.get") as mock_get,
    ):
        # Mocking the external dependencies
        mock_get.return_value = "mock_model_path"
        mock_recognizer = MagicMock()
        mock_initialize_recognizer.return_value = mock_recognizer
        mock_raw_input_stream.return_value.__enter__.return_value = (
            MagicMock()
        )  # Mock the context manager of the stream

        # Return all the mocks as a dictionary for easy access
        yield {
            "mock_get": mock_get,
            "mock_initialize_recognizer": mock_initialize_recognizer,
            "mock_do_once": mock_do_once,
            "mock_raw_input_stream": mock_raw_input_stream,
            "mock_process_text_and_communicate": mock_process_text_and_communicate,
            "mock_process_audio_data": mock_process_audio_data,
            "mock_flush_queue": mock_flush_queue,
        }


# Test case 1: Normal processing


def test_cli_talk(cli_talk_mocks):
    """
    Simulates a test case for a CLI talk function with voice feature enabled.

    Arguments:
    - cli_talk_mocks: A MagicMock object containing mocks for CLI talk functionality.

    Side Effects:
    - Modifies the `args` object by setting the 'voice' attribute to True.
    """

    # Test case where `args` has 'voice'
    args = MagicMock()
    args.voice = True

    # Simulate successful audio data processing and AI communication
    cli_talk_mocks["mock_process_audio_data"].return_value = "Valid Text"
    # Simulating that the text is not "stop"
    cli_talk_mocks["mock_process_text_and_communicate"].return_value = False

    # Simulate do_once returning False for a couple of iterations and then True
    cli_talk_mocks["mock_do_once"].side_effect = [
        False,
        False,
        True,
    ]  # Loop will break after 2 iterations

    # Call the function
    cli_talk(MagicMock(), args)

    # Ensure the callback puts data in the queue
    cli_talk_mocks["mock_process_audio_data"].assert_called()

    # Ensure the AI helper was called with the correct arguments and the loop breaks
    cli_talk_mocks["mock_process_text_and_communicate"].assert_called()

    # Assert that flush_queue was called
    cli_talk_mocks["mock_flush_queue"].assert_called()


# Test case 2: Invalid audio data


def test_cli_talk_invalid_audio(cli_talk_mocks):
    """
    Test the CLI talk function with invalid audio input.

    Arguments:
    - cli_talk_mocks: Mock objects for CLI talk function testing.

    Side Effects:
    - Sets up a mock object for the CLI talk function testing.
    """

    # Test case where `args` has 'voice'
    args = MagicMock()
    args.voice = True

    # Simulate invalid audio data (i.e., `process_audio_data` returns None)
    cli_talk_mocks["mock_process_audio_data"].return_value = None

    # Simulate do_once returning False for a couple of iterations and then True
    cli_talk_mocks["mock_do_once"].side_effect = [
        False,
        False,
        True,
    ]  # Loop will break after 2 iterations

    # Call the function
    cli_talk(MagicMock(), args)

    # Ensure that the loop stops when do_once returns True after 2 iterations
    cli_talk_mocks["mock_process_audio_data"].assert_called()


# Test case 3: Loop breaks on successful AI communication


def test_cli_talk_breaks_loop(cli_talk_mocks):
    """
    Simulates a test case where the 'voice' argument is set to True in a CLI talk function.

    Arguments:
    - cli_talk_mocks: Mock object used for testing CLI talk functionality.

    Side Effects:
    - Initializes a MagicMock object to simulate command line arguments with the 'voice' attribute set to True.
    """

    # Test case where `args` has 'voice'
    args = MagicMock()
    args.voice = True

    # Simulate successful audio data processing and AI communication
    cli_talk_mocks["mock_process_audio_data"].return_value = "Valid Text"
    # This should cause the break in the loop
    cli_talk_mocks["mock_process_text_and_communicate"].return_value = True

    # Simulate do_once returning False for a couple of iterations and then True
    cli_talk_mocks["mock_do_once"].side_effect = [
        False,
        False,
        True,
    ]  # Loop will break after 2 iterations

    # Call the function
    cli_talk(MagicMock(), args)

    # Assert the voice flag is set correctly
    assert args.voice is True

    # Ensure the callback puts data in the queue
    cli_talk_mocks["mock_process_audio_data"].assert_called()

    # Simulate the loop stopping when do_once returns True after 2 iterations
    cli_talk_mocks["mock_process_audio_data"].assert_called()
    cli_talk_mocks["mock_do_once"].assert_called()


def test_callback():
    """
    Create a mock queue for testing purposes.
    """

    # Create a mock queue
    mock_queue = MagicMock()

    # Simulate input data
    indata = b"test audio data"  # Sample byte data for testing
    frames = 100  # Arbitrary value for frames
    time = 1.0  # Arbitrary value for time
    status = None  # No status needed for this test

    # Call the callback function
    callback(indata, frames, time, status, mock_queue)

    # Verify that the queue's put method was called with the correct data
    mock_queue.put.assert_called_once_with(indata)
