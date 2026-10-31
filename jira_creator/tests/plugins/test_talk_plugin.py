"""Tests for the talk plugin, driven through its public execute() entry point."""

import json
import os
import queue
import sys
import types
from argparse import ArgumentParser, Namespace
from unittest.mock import MagicMock, patch

import pytest

from jira_creator.plugins.talk_plugin import TalkError, TalkPlugin, suppress_stderr

MODULE = "jira_creator.plugins.talk_plugin"


def fake_recognizer(model, rate):
    """Vosk recogniser: empty audio is 'not a full phrase', otherwise echo it."""
    heard = {"last": b"", "model": model, "rate": rate}

    def accept(data):
        heard["last"] = data
        return data != b""

    def result():
        return json.dumps({"text": heard["last"].decode()})

    recognizer = MagicMock()
    recognizer.AcceptWaveform.side_effect = accept
    recognizer.Result.side_effect = result
    return recognizer


class ScriptedQueue:
    """Audio queue that yields a fixed script of utterances."""

    def __init__(self, script, leftovers=0):
        self.script = list(script)
        self.leftovers = leftovers
        self.flushed = 0

    def put(self, item):
        """Queue an item first."""
        self.script.insert(0, item)

    def get(self):
        """Next utterance."""
        return self.script.pop(0)

    def empty(self):
        """True once leftovers are drained."""
        return self.leftovers == 0

    def get_nowait(self):
        """Drain one leftover block."""
        self.flushed += 1
        if self.leftovers < 0:
            self.leftovers = 0
            raise queue.Empty
        self.leftovers -= 1


class FakeStream:
    """Microphone stream that delivers one silent block on start."""

    def __init__(self, callback, **kwargs):
        self.callback = callback
        self.kwargs = kwargs

    def __enter__(self):
        self.callback(b"", 0, None, None)
        return self

    def __exit__(self, *exc):
        return False


class FakeW2N:
    """word2number stand-in that can be told to reject a word."""

    WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")

    def __init__(self, rejects=()):
        self.rejects = set(rejects)

    def word_to_num(self, word):
        """Digit word to int."""
        if word in self.rejects:
            raise ValueError(word)
        return self.WORDS.index(word)


@pytest.fixture(name="env")
def env_fixture(tmp_path):
    """EnvFetcher values with a Vosk model directory that exists."""
    values = {"JIRA_VOSK_MODEL": str(tmp_path), "JIRA_PROJECT_KEY": "AAP"}
    with patch(f"{MODULE}.EnvFetcher.get", side_effect=lambda k, default=None: values.get(k, default)):
        yield values


@pytest.fixture(name="audio")
def audio_fixture(monkeypatch, env):
    """Install fake audio/speech modules and return a runner for execute()."""
    w2n = FakeW2N()
    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(RawInputStream=FakeStream))
    monkeypatch.setitem(
        sys.modules, "vosk", types.SimpleNamespace(Model=lambda path: path, KaldiRecognizer=fake_recognizer)
    )
    monkeypatch.setitem(sys.modules, "word2number", types.SimpleNamespace(w2n=w2n))

    ai_helper = MagicMock()
    registry = MagicMock()
    registry.get_plugin.return_value = ai_helper

    def run(script, voice=False, leftovers=0):
        """Run execute() over a script of utterances ending in stop."""
        q = ScriptedQueue(list(script) + [b"stop"], leftovers)
        with (
            patch(f"{MODULE}.queue.Queue", return_value=q),
            patch("jira_creator.core.plugin_registry.PluginRegistry", return_value=registry),
        ):
            assert TalkPlugin().execute(MagicMock(), Namespace(voice=voice)) is True
        return q

    return types.SimpleNamespace(run=run, w2n=w2n, ai_helper=ai_helper, registry=registry, env=env)


def prompts(audio):
    """Prompts passed to the AI helper, in order."""
    return [c.args[1].prompt for c in audio.ai_helper.execute.call_args_list]


class TestPluginMetadata:
    """Static plugin information."""

    def test_properties(self):
        """Command metadata is fixed."""
        plugin = TalkPlugin()
        assert plugin.command_name == "talk"
        assert "voice" in plugin.help_text.lower()
        assert plugin.category == "Utilities"
        assert plugin.example_commands == ["talk", "talk --voice"]
        assert plugin.get_plugin_exceptions() == {"TalkError": TalkError}
        assert not plugin.rest_operation(MagicMock(), anything=1)

    @pytest.mark.parametrize(("argv", "voice"), [([], False), (["--voice"], True)])
    def test_register_arguments(self, argv, voice):
        """--voice is an optional flag."""
        parser = ArgumentParser()
        TalkPlugin().register_arguments(parser)
        assert parser.parse_args(argv).voice is voice

    def test_suppress_stderr_restores_fd(self):
        """stderr is restored after suppression."""
        before = os.fstat(2)
        with suppress_stderr():
            os.write(2, b"hidden\n")
        assert os.fstat(2).st_ino == before.st_ino


class TestExecuteErrors:
    """Dependency and configuration failures surface as TalkError."""

    @pytest.mark.parametrize("missing", ["sounddevice", "vosk", "word2number"])
    def test_missing_dependency(self, audio, monkeypatch, missing, capsys):
        """Any missing speech module is reported."""
        monkeypatch.setitem(sys.modules, missing, None)
        with pytest.raises(TalkError, match="Missing required dependencies"):
            TalkPlugin().execute(MagicMock(), Namespace(voice=False))
        audio.ai_helper.execute.assert_not_called()
        assert "❌ Talk command failed" in capsys.readouterr().out

    @pytest.mark.parametrize("model", ["", "/does/not/exist"])
    def test_model_not_found(self, audio, model):
        """An unset or absent model path is reported."""
        audio.env["JIRA_VOSK_MODEL"] = model
        with pytest.raises(TalkError, match="Vosk model not found"):
            TalkPlugin().execute(MagicMock(), Namespace(voice=False))


class TestListening:
    """Speech loop behaviour."""

    def test_stop_ends_session(self, audio, capsys):
        """Saying stop ends the session without AI calls."""
        audio.run([])
        out = capsys.readouterr().out
        assert "🎤 Listening" in out
        assert "📝 Heard: stop" in out
        assert "👋 Goodbye!" in out
        audio.ai_helper.execute.assert_not_called()

    def test_short_command_rejected(self, audio, capsys):
        """Phrases under four words are not sent."""
        audio.run([b"hello there"])
        assert "Command too short" in capsys.readouterr().out
        audio.ai_helper.execute.assert_not_called()

    def test_silence_and_blank_text_ignored(self, audio, capsys):
        """Silence and blank results are skipped."""
        audio.run([b"", b"   "])
        out = capsys.readouterr().out
        assert out.count("📝 Heard:") == 1
        audio.ai_helper.execute.assert_not_called()

    @pytest.mark.parametrize("voice", [False, True])
    def test_command_sent_to_ai_helper(self, audio, voice, capsys):
        """A full command reaches the AI helper normalised."""
        audio.run([b"add issue four three two one in sprint"], voice=voice)
        args = audio.ai_helper.execute.call_args.args[1]
        assert args == Namespace(prompt="add AAP-4321 in sprint", voice=voice, no_ai=False)
        assert "🔄 Normalized: add AAP-4321 in sprint" in capsys.readouterr().out
        audio.registry.discover_plugins.assert_called_once()
        audio.registry.get_plugin.assert_called_once_with("ai-helper")

    @pytest.mark.parametrize("leftovers", [2, -1])
    def test_queue_flushed_after_phrase(self, audio, leftovers):
        """Leftover audio is drained after each phrase."""
        q = audio.run([b"show me issue one two"], leftovers=leftovers)
        assert q.flushed >= 1

    def test_ai_helper_missing(self, audio, capsys):
        """A missing AI helper is reported."""
        audio.registry.get_plugin.return_value = None
        audio.run([b"show me issue one two"])
        assert "AI helper plugin not found" in capsys.readouterr().out

    @pytest.mark.parametrize("error", [ValueError("bad"), KeyError("k"), AttributeError("a")])
    def test_ai_helper_failure_reported(self, audio, error, capsys):
        """AI helper errors are reported, not raised."""
        audio.ai_helper.execute.side_effect = error
        audio.run([b"show me issue one two"])
        assert "❌ Failed to process command" in capsys.readouterr().out


class TestNormalisation:
    """Spoken issue references reach the AI helper normalised."""

    @pytest.mark.parametrize(
        ("spoken", "expected"),
        [
            ("assign issue for free to me", "assign AAP-432 me"),  # "to" is heard as "two"
            ("close issue won too ate now", "close AAP-128 now"),
            ("please look at the issue later", "please look at the issue later"),
            ("issue nine tirty fifty and issue fife", "AAP-935 and AAP-5"),
            ("set priority of issue to high", "set priority of AAP-2 high"),
        ],
    )
    def test_issue_references(self, audio, spoken, expected):
        """Spoken digits become issue keys."""
        audio.run([spoken.encode()])
        assert prompts(audio) == [expected]

    def test_project_key_from_env(self, audio):
        """The project key comes from the environment."""
        audio.env["JIRA_PROJECT_KEY"] = "XYZ"
        audio.run([b"show me issue seven seven"])
        assert prompts(audio) == ["show me XYZ-77"]

    def test_unconvertible_digit_word_kept(self, audio):
        """Digit words w2n rejects are kept as words."""
        audio.w2n.rejects.add("three")
        audio.run([b"show me issue three one"])
        assert prompts(audio) == ["show me issue three 1"]
