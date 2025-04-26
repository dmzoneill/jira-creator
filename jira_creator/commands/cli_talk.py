#!/usr/bin/env python
"""
This module provides functionality for processing audio input and converting spoken digit words into numerical
representations, while also handling issue references in a specified format.

Key features include:
- A context manager to suppress standard error output.
- Functions to clean up fuzzy digit words, convert digit words to numbers, and normalize issue references.
- Audio processing capabilities using the VOSK speech recognition model.
- Integration with a command-line interface (CLI) to interact with an AI system based on recognized speech.

Functions:
- `suppress_stderr`: Context manager to suppress standard error output.
- `fuzzy_digit_cleanup`: Corrects fuzzy digit words in the input text.
- `word_digits_to_numbers`: Converts digit words to their numeric representations.
- `combine_consecutive_digits`: Combines sequences of digit strings into a single string.
- `normalize_issue_references`: Normalizes issue references in the text to a specified format.
- `flush_queue`: Clears a queue of audio data.
- `do_once`: Placeholder function that returns False.
- `initialize_recognizer`: Initializes the VOSK recognizer model.
- `process_text_and_communicate`: Normalizes input text and communicates with an AI system.
- `process_audio_data`: Processes audio data from a queue and returns recognized text.
- `callback`: Handles audio input stream callback.
- `cli_talk`: Main function to listen for audio input, process it, and communicate with the AI.

Dependencies:
- `sounddevice`: For audio input handling.
- `vosk`: For speech recognition.
- `word2number`: For converting words to numbers.
- `core.env_fetcher`: For fetching environment variables.
"""

# pylint: disable=too-few-public-methods

import contextlib
import json
import os
import queue
from argparse import Namespace
from typing import Any, Optional

import sounddevice
from core.env_fetcher import EnvFetcher
from vosk import KaldiRecognizer, Model
from word2number import w2n


@contextlib.contextmanager
def suppress_stderr() -> None:
    """
    Suppresses the standard error (stderr) output temporarily by redirecting it to /dev/null.
    """
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        old_stderr = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(old_stderr, 2)


DIGIT_WORDS = {
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
}

FUZZY_DIGIT_MAP = {
    "for": "four",
    "free": "three",
    "tree": "three",
    "won": "one",
    "to": "two",
    "too": "two",
    "fife": "five",
    "ate": "eight",
    "twenty": "two",
    "tirty": "three",
    "forty": "four",
    "fifty": "five",
    "sixty": "six",
    "seventy": "seven",
    "eighty": "eight",
    "ninety": "nine",
}


def fuzzy_digit_cleanup(text: str) -> str:
    """
    Cleans up fuzzy digits in a text by replacing them with their correct counterparts.

    Arguments:
    - text (str): The input text containing fuzzy digits to be cleaned up.

    Return:
    - str: The text with fuzzy digits replaced by their correct counterparts.
    """
    tokens = text.split()
    corrected = [FUZZY_DIGIT_MAP.get(t, t) for t in tokens]
    return " ".join(corrected)


def word_digits_to_numbers(text: str) -> str:
    """
    Converts digit words to individual digits in a given text.

    Arguments:
    - text (str): A string containing words representing digits, e.g., 'four three'.

    Return:
    - str: A string with digit words replaced by their corresponding digits, e.g., '4 3'.

    Note:
    - The function uses a predefined set of digit words (DIGIT_WORDS) and the word2number library (w2n) to convert
    words to numbers.
    """
    tokens = text.split()
    result = []

    for token in tokens:
        if token in DIGIT_WORDS:
            result.append(str(w2n.word_to_num(token)))
        else:
            result.append(token)

    return " ".join(result)


def combine_consecutive_digits(text: str) -> str:
    """
    Combine sequences of digits in a given text by removing spaces between consecutive digits.

    Arguments:
    - text (str): A string containing alphanumeric characters.

    Return:
    - str: A modified string where sequences of digits have been combined by removing spaces between consecutive digits.
    """
    tokens = text.split()
    result = []
    buffer = []

    for token in tokens:
        if token.isdigit():
            buffer.append(token)
        else:
            if buffer:
                result.append("".join(buffer))
                buffer = []
            result.append(token)

    if buffer:
        result.append("".join(buffer))

    return " ".join(result)


def normalize_issue_references(text: str) -> str:
    """
    Convert all 'issue <digits>' references to 'PROJECTKEY-<digits>' with fuzzy support.

    Arguments:
    - text (str): The input text containing issue references to be normalized.

    Return:
    - str: The text with normalized issue references.

    Side Effects:
    - Uses EnvFetcher to get the project key. If not available, defaults to "AAP".
    - Calls fuzzy_digit_cleanup to clean up the text.
    - Calls word_digits_to_numbers to convert word digits to numbers.
    - Modifies the input text by replacing 'issue <digits>' references with 'PROJECTKEY-<digits>'.
    """
    project_key = EnvFetcher.get("PROJECT_KEY") or "AAP"

    text = fuzzy_digit_cleanup(text)
    text = word_digits_to_numbers(text)

    tokens = text.split()
    result = []
    i = 0

    while i < len(tokens):
        if tokens[i] == "issue":
            digit_buffer = []
            j = i + 1

            while j < len(tokens):
                if tokens[j].isdigit():
                    digit_buffer.append(tokens[j])
                else:
                    break
                j += 1

            if digit_buffer:
                issue_key = f"{project_key}-" + "".join(digit_buffer)
                result.append(issue_key)
                i = j
            else:
                result.append(tokens[i])
                i += 1
        else:
            result.append(tokens[i])
            i += 1

    return " ".join(result)


def flush_queue(q: queue.Queue) -> None:
    """
    Clears all elements from the queue provided as input.

    Arguments:
    - q (queue.Queue): A queue object from which all elements will be removed.

    Side Effects:
    - Modifies the queue provided as input by removing all elements.

    Exceptions:
    - No exceptions are raised.
    """
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break


def do_once() -> bool:
    """
    This function returns a boolean value False.
    """
    return False


def initialize_recognizer() -> KaldiRecognizer:
    """
    Initializes the recognizer with the VOSK model.

    Returns:
    KaldiRecognizer: An instance of the KaldiRecognizer class initialized with the VOSK model.
    """
    model = Model(EnvFetcher.get("VOSK_MODEL"))
    rec = KaldiRecognizer(model, 16000)
    return rec


def process_text_and_communicate(text: str, cli: object, voice: bool) -> bool:
    """
    Normalizes the text by removing any issue references and splits it into words for further processing.

    Arguments:
    - text (str): The input text to be processed.
    - cli (object): An object representing the command line interface.
    - voice (bool): A boolean indicating whether voice communication is enabled.

    Return:
    - bool: Returns True if the normalized text ends with 'stop', False if the number of words in the text is less than
    4, otherwise returns False.

    Side Effects:
    - Modifies the text by removing issue references.
    - Prints the message "Talking to AI: <text>".
    """
    text = normalize_issue_references(text)
    words = text.strip().split()

    if text.lower().endswith("stop"):
        return True

    if len(words) < 4:
        return False

    print("Talking to AI: " + text)

    class Args:
        """Dummy namespace object for test"""

        prompt: str
        voice: bool

    args = Args()
    args.prompt = text
    args.voice = voice
    cli.ai_helper(args)

    return False


def process_audio_data(q: queue.Queue, rec: KaldiRecognizer) -> Optional[str]:
    """
    Processes the audio data from the queue and returns the recognized text.

    Arguments:
    - q (queue.Queue): A queue containing audio data to process.
    - rec (KaldiRecognizer): An instance of KaldiRecognizer used for recognizing audio data.

    Return:
    - Optional[str]: The recognized text as a string, or None if no text was recognized.
    """
    data = q.get()
    if not rec.AcceptWaveform(data):
        return None

    result = json.loads(rec.Result())
    original = result.get("text", "")

    if len(original) <= 0:
        return None

    return original.strip()


def callback(indata: bytes, _: int, __: object, ___: object, q: queue.Queue) -> None:
    """
    Handles the callback for the audio stream.

    Arguments:
    - indata (bytes): The audio data received as bytes.
    - _: (int): An unused parameter.
    - __: (object): An unused parameter.
    - ___: (object): An unused parameter.
    - q (queue.Queue): A queue to store the audio data.

    Return:
    - None
    """
    q.put(bytes(indata))


def cli_talk(cli: Any, args: Namespace) -> None:
    """
    Creates a queue object to store items for communication between a command-line interface (CLI) and a function.

    Arguments:
    - cli (Any): An object representing the command-line interface (CLI).
    - args (Namespace): An object containing arguments passed to the function.

    Side Effects:
    - Initializes a queue object to store communication items.
    - Initializes a voice flag based on the presence of the "voice" attribute in the args namespace.
    - Initializes a recognizer for audio processing.
    - Opens a RawInputStream for audio input processing.
    - Prints "Listening: " to the console.
    - Continuously processes audio data, communicates with the CLI based on the processed text, and flushes the queue.

    Exceptions:
    - suppress_stderr(): Suppresses standard error output during the execution.

    Note: The function does not have a return value.
    """
    q = queue.Queue()
    voice = bool(hasattr(args, "voice"))

    with suppress_stderr():
        rec = initialize_recognizer()

        with sounddevice.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=lambda indata, frames, time, status: callback(
                indata, frames, time, status, q
            ),
        ):
            print("Listening: ")
            while do_once() is False:
                text = process_audio_data(q, rec)
                if text and process_text_and_communicate(text, cli, voice):
                    break
                flush_queue(q)
