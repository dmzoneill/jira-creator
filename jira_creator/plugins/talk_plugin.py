#!/usr/bin/env python
"""
Talk plugin for jira-creator.

This plugin allows users to interact with Jira using voice input via microphone.
Uses Vosk for speech recognition and converts spoken commands to text.
"""

import contextlib
import json
import os
import queue
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin

logger = get_logger("talk")


@contextlib.contextmanager
def suppress_stderr():
    """Suppress stderr output (for Vosk model loading)."""
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        old_stderr = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(old_stderr, 2)


# Digit word mappings
DIGIT_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}

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


class TalkError(Exception):
    """Exception raised when voice/talk operation fails."""


class TalkPlugin(JiraPlugin):
    """Plugin for voice interaction with Jira using microphone."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "talk"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Use voice commands to interact with Jira (requires microphone)"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Utilities"

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "TalkError": TalkError,
        }

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["talk", "talk --voice"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("--voice", action="store_true", help="Enable text-to-speech responses")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the talk command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Check dependencies
            self._check_dependencies()

            # Initialize speech recognition
            rec = self._initialize_recognizer()

            # Start listening
            self._listen_and_process(client, rec, args.voice)

            return True

        except TalkError as e:
            logger.error("Talk command failed: %s", e)
            print(f"❌ Talk command failed: {e}")
            raise

    def _check_dependencies(self) -> None:
        """Check if required dependencies are installed."""
        try:
            import sounddevice  # pylint: disable=import-outside-toplevel,unused-import
            import vosk  # pylint: disable=import-outside-toplevel,unused-import
            from word2number import w2n  # pylint: disable=import-outside-toplevel,unused-import

            # Verify imports are available
            _ = sounddevice, vosk, w2n
        except ImportError as e:
            raise TalkError(
                f"Missing required dependencies: {e}. " "Install with: pipenv install sounddevice vosk word2number"
            ) from e

        # Check if Vosk model is configured
        vosk_model = EnvFetcher.get("JIRA_VOSK_MODEL", default="")
        if not vosk_model or not os.path.exists(vosk_model):
            raise TalkError(
                f"Vosk model not found at: {vosk_model}. "
                "Download from https://alphacephei.com/vosk/models and set JIRA_VOSK_MODEL"
            )

    def _initialize_recognizer(self):
        """Initialize the Vosk speech recognizer."""
        from vosk import KaldiRecognizer, Model  # pylint: disable=import-error,import-outside-toplevel

        vosk_model_path = EnvFetcher.get("JIRA_VOSK_MODEL")
        logger.info("Loading Vosk model from: %s", vosk_model_path)

        with suppress_stderr():
            model = Model(vosk_model_path)
            rec = KaldiRecognizer(model, 16000)

        logger.info("Vosk model loaded successfully")
        return rec

    def _listen_and_process(self, client: Any, rec: Any, voice: bool) -> None:
        """
        Listen to microphone and process speech.

        Arguments:
            client: JiraClient instance
            rec: Vosk recognizer
            voice: Whether to use text-to-speech
        """
        import sounddevice

        q = queue.Queue()

        def callback(indata, frames, time, status):  # pylint: disable=unused-argument
            """Audio callback."""
            q.put(bytes(indata))

        print("🎤 Listening... (say 'stop' to exit)")
        print("   Example: 'Add issue four three two one to the current sprint'")

        with suppress_stderr():
            with sounddevice.RawInputStream(
                samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback
            ):
                while True:
                    # Get audio data
                    data = q.get()

                    # Process with Vosk
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").strip()

                        if not text:
                            continue

                        print(f"\n📝 Heard: {text}")

                        # Check for stop command
                        if "stop" in text.lower():
                            print("👋 Goodbye!")
                            break

                        # Process the text
                        if len(text.split()) >= 4:  # Require at least 4 words
                            normalized_text = self._normalize_issue_references(text)
                            print(f"🔄 Normalized: {normalized_text}")

                            # Call AI helper with the normalized text
                            self._call_ai_helper(client, normalized_text, voice)
                        else:
                            print("   ⚠️  Command too short, please be more specific")

                    # Flush queue
                    while not q.empty():
                        try:
                            q.get_nowait()
                        except queue.Empty:
                            break

    def _normalize_issue_references(self, text: str) -> str:
        """
        Normalize issue references in spoken text.

        Converts: "issue four three two one" -> "AAP-4321"

        Arguments:
            text: Original text

        Returns:
            Normalized text
        """
        from word2number import w2n  # pylint: disable=import-error,import-outside-toplevel

        project_key = EnvFetcher.get("JIRA_PROJECT_KEY", default="AAP")

        # Step 1: Fuzzy digit word correction
        text = self._fuzzy_digit_cleanup(text)

        # Step 2: Convert digit words to digits
        text = self._word_digits_to_numbers(text, w2n)

        # Step 3: Normalize "issue <digits>" to "PROJECTKEY-<digits>"
        tokens = text.split()
        result = []
        i = 0

        while i < len(tokens):
            if tokens[i] == "issue":
                digit_buffer = []
                j = i + 1

                # Collect consecutive digits
                while j < len(tokens) and tokens[j].isdigit():
                    digit_buffer.append(tokens[j])
                    j += 1

                # If we found digits, create issue key
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

    def _fuzzy_digit_cleanup(self, text: str) -> str:
        """Apply fuzzy digit word corrections."""
        tokens = text.split()
        corrected = [FUZZY_DIGIT_MAP.get(t, t) for t in tokens]
        return " ".join(corrected)

    def _word_digits_to_numbers(self, text: str, w2n) -> str:
        """Convert digit words to individual digits: 'four three' → '4 3'."""
        tokens = text.split()
        result = []

        for token in tokens:
            if token in DIGIT_WORDS:
                try:
                    result.append(str(w2n.word_to_num(token)))
                except ValueError:
                    result.append(token)
            else:
                result.append(token)

        return " ".join(result)

    def _call_ai_helper(self, client: Any, text: str, voice: bool) -> None:
        """
        Call AI helper with the transcribed text.

        Arguments:
            client: JiraClient instance
            text: Normalized text
            voice: Whether to use text-to-speech
        """
        from jira_creator.core.plugin_registry import PluginRegistry

        # Get AI helper plugin
        registry = PluginRegistry()
        registry.discover_plugins()
        ai_helper = registry.get_plugin("ai-helper")

        if not ai_helper:
            print("   ⚠️  AI helper plugin not found")
            return

        # Create args for AI helper
        args = Namespace(prompt=text, voice=voice, no_ai=False)

        # Execute AI helper
        try:
            ai_helper.execute(client, args)
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("AI helper execution failed: %s", e)
            print(f"   ❌ Failed to process command: {e}")

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        This plugin doesn't use REST operations directly.

        Arguments:
            client: JiraClient instance
            **kwargs: Additional arguments

        Returns:
            Empty dict
        """
        return {}
