import contextlib
import json
import os
import queue

import sounddevice
from core.env_fetcher import EnvFetcher
from vosk import KaldiRecognizer, Model
from word2number import w2n


@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, "w") as devnull:
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
    tokens = text.split()
    corrected = [FUZZY_DIGIT_MAP.get(t, t) for t in tokens]
    return " ".join(corrected)


def word_digits_to_numbers(text: str) -> str:
    """Convert digit words to individual digits: 'four three' → '4 3'"""
    tokens = text.split()
    result = []

    for token in tokens:
        if token in DIGIT_WORDS:
            result.append(str(w2n.word_to_num(token)))
        else:
            result.append(token)

    return " ".join(result)


def combine_consecutive_digits(text: str) -> str:
    """Combine sequences of digits: '4 3 2 1' → '4321'"""
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
    """Convert all 'issue <digits>' references to 'PROJECTKEY-<digits>' with fuzzy support."""
    project_key = EnvFetcher.get("PROJECT_KEY") or "AAP"

    # Step 0: Fuzzy digit word correction
    text = fuzzy_digit_cleanup(text)

    # Step 1: Convert digit words to digits
    text = word_digits_to_numbers(text)

    # Step 2: Tokenize
    tokens = text.split()

    result = []
    i = 0

    while i < len(tokens):
        if tokens[i] == "issue":
            digit_buffer = []
            j = i + 1

            # Collect digits until a non-digit is encountered
            while j < len(tokens):
                if tokens[j].isdigit():
                    digit_buffer.append(tokens[j])  # Collect digits
                else:
                    break  # Stop collecting when a non-digit is encountered
                j += 1

            # If we found digits after 'issue', process them
            if digit_buffer:
                issue_key = f"{project_key}-" + "".join(digit_buffer)
                result.append(issue_key)
                i = j  # Skip past what we've consumed
            else:
                result.append(tokens[i])
                i += 1
        else:
            result.append(tokens[i])
            i += 1

    return " ".join(result)


def flush_queue(q):
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break


def do_once():
    return False


def initialize_recognizer():
    """Initializes the recognizer with the VOSK model."""
    model = Model(EnvFetcher.get("VOSK_MODEL"))
    rec = KaldiRecognizer(model, 16000)
    return rec


def process_text_and_communicate(text, cli, voice):
    """Normalizes the text and interacts with AI."""
    text = normalize_issue_references(text)
    words = text.strip().split()

    if text.lower().endswith("stop"):
        return True

    if len(words) < 4:
        return False

    print("Talking to AI: " + text)

    class Args:
        prompt: str
        voice: bool

    args = Args()
    args.prompt = text
    args.voice = voice
    cli.ai_helper(args)

    return False


def process_audio_data(q, rec):
    """Processes the audio data from the queue and returns the recognized text."""
    data = q.get()
    if not rec.AcceptWaveform(data):
        return None

    result = json.loads(rec.Result())
    original = result.get("text", "")

    if len(original) <= 0:
        return None

    return original.strip()


def callback(indata, frames, time, status, q):
    """Handles the callback for the audio stream."""
    q.put(bytes(indata))


def cli_talk(cli, args):
    q = queue.Queue()

    voice = True if hasattr(args, "voice") else False

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
            while True and do_once() is False:
                text = process_audio_data(q, rec)
                if text and process_text_and_communicate(text, cli, voice):
                    break
                flush_queue(q)
