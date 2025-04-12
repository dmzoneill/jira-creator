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
    assert do_once() is False


def test_cli_exec(cli, cli_talk_mocks):
    class Args:
        prompt: str
        voice: bool

    cli.talk(Args())


# Test Case 1: fuzzy_digit_cleanup
def test_fuzzy_digit_cleanup():
    assert fuzzy_digit_cleanup("I have forty apples") == "I have four apples"
    assert fuzzy_digit_cleanup("I have tirty oranges") == "I have three oranges"
    assert fuzzy_digit_cleanup("I see a tree") == "I see a three"
    assert fuzzy_digit_cleanup("My phone number is won") == "My phone number is one"
    assert fuzzy_digit_cleanup("I ate twenty cookies") == "I eight two cookies"


# Test Case 2: word_digits_to_numbers
def test_word_digits_to_numbers():
    assert word_digits_to_numbers("I have four apples") == "I have 4 apples"
    assert word_digits_to_numbers("I have three oranges") == "I have 3 oranges"
    assert word_digits_to_numbers("I see five trees") == "I see 5 trees"
    assert (
        word_digits_to_numbers("My address is nine street") == "My address is 9 street"
    )


# Test Case 3: combine_consecutive_digits
def test_combine_consecutive_digits():
    assert combine_consecutive_digits("4 3 2 1") == "4321"
    assert combine_consecutive_digits("7 5") == "75"
    assert combine_consecutive_digits("1 2 3") == "123"
    assert combine_consecutive_digits("I have 1 0 0 0 dollars") == "I have 1000 dollars"


# Test Case 4: normalize_issue_references
def test_normalize_issue_references():
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
    q = queue.Queue()
    q.put("item1")
    q.put("item2")

    flush_queue(q)

    assert q.empty()


# Test Case 8: suppress_stderr
def test_suppress_stderr():
    with suppress_stderr():
        print("This should not be printed", file=sys.stderr)

    assert True


# Test Case: initialize_recognizer - Verifies that the recognizer is initialized correctly
@patch("commands.cli_talk.Model")
@patch("commands.cli_talk.KaldiRecognizer")
def test_initialize_recognizer(MockKaldiRecognizer, MockModel):
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
    text = "Stop"
    voice = True

    # Call the function
    result = process_text_and_communicate(text, cli, voice)

    # Ensure ai_helper is not called (as the text is 'stop')
    cli.ai_provider.improve_text.assert_not_called()

    # Assert that the function returns True (ends when 'stop' is in the text)
    assert result


def test_process_text_and_communicate_too_few_words(cli):
    text = "Too few words"
    voice = True

    result = process_text_and_communicate(text, cli, voice)

    # Assert that the function returns False (as there are not enough words)
    assert not result


# Test Case: process_audio_data - Verifies correct audio data processing


@patch("json.loads")
def test_process_audio_data_valid(mock_json_loads):
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
