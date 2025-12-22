#!/usr/bin/env python
"""Tests for the talk plugin."""

import json
from argparse import Namespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from jira_creator.plugins.talk_plugin import TalkError, TalkPlugin, suppress_stderr


class TestSuppressStderr:
    """Test suppress_stderr context manager."""

    def test_suppress_stderr(self):
        """Test that stderr is suppressed."""
        with suppress_stderr():
            # This would normally write to stderr but should be suppressed
            pass


class TestTalkPlugin:
    """Test cases for TalkPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = TalkPlugin()
        assert plugin.command_name == "talk"
        assert plugin.help_text == "Use voice commands to interact with Jira (requires microphone)"
        assert plugin.category == "Utilities"
        assert len(plugin.example_commands) == 2

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = TalkPlugin()
        parser = Mock()
        plugin.register_arguments(parser)
        parser.add_argument.assert_called_once_with(
            "--voice", action="store_true", help="Enable text-to-speech responses"
        )

    def test_rest_operation(self):
        """Test rest_operation returns empty dict."""
        plugin = TalkPlugin()
        mock_client = Mock()
        result = plugin.rest_operation(mock_client)
        assert result == {}

    @patch("jira_creator.plugins.talk_plugin.os.path.exists")
    @patch("jira_creator.plugins.talk_plugin.EnvFetcher")
    def test_check_dependencies_success(self, mock_env, mock_exists):
        """Test successful dependency check."""
        plugin = TalkPlugin()
        mock_env.get.return_value = "/path/to/model"
        mock_exists.return_value = True

        # Mock the imported modules
        mock_sounddevice = Mock()
        mock_vosk = Mock()
        mock_w2n_module = Mock()

        with patch.dict(
            "sys.modules",
            {"sounddevice": mock_sounddevice, "vosk": mock_vosk, "word2number": Mock(w2n=mock_w2n_module)},
        ):
            # Should not raise
            plugin._check_dependencies()

    @patch("jira_creator.plugins.talk_plugin.os.path.exists")
    @patch("jira_creator.plugins.talk_plugin.EnvFetcher")
    def test_check_dependencies_model_not_found(self, mock_env, mock_exists):
        """Test dependency check when model not found."""
        plugin = TalkPlugin()
        mock_env.get.return_value = "/path/to/model"
        mock_exists.return_value = False

        mock_sounddevice = Mock()
        mock_vosk = Mock()
        mock_w2n_module = Mock()

        with patch.dict(
            "sys.modules",
            {"sounddevice": mock_sounddevice, "vosk": mock_vosk, "word2number": Mock(w2n=mock_w2n_module)},
        ):
            with pytest.raises(TalkError, match="Vosk model not found"):
                plugin._check_dependencies()

    @patch("jira_creator.plugins.talk_plugin.os.path.exists")
    @patch("jira_creator.plugins.talk_plugin.EnvFetcher")
    def test_check_dependencies_model_empty(self, mock_env, mock_exists):
        """Test dependency check when model path is empty."""
        plugin = TalkPlugin()
        mock_env.get.return_value = ""

        mock_sounddevice = Mock()
        mock_vosk = Mock()
        mock_w2n_module = Mock()

        with patch.dict(
            "sys.modules",
            {"sounddevice": mock_sounddevice, "vosk": mock_vosk, "word2number": Mock(w2n=mock_w2n_module)},
        ):
            with pytest.raises(TalkError, match="Vosk model not found"):
                plugin._check_dependencies()

    @patch("jira_creator.plugins.talk_plugin.EnvFetcher")
    def test_initialize_recognizer(self, mock_env):
        """Test recognizer initialization."""
        plugin = TalkPlugin()
        mock_env.get.return_value = "/path/to/model"

        mock_model = Mock()
        mock_recognizer = Mock()
        mock_vosk = Mock()
        mock_vosk.Model.return_value = mock_model
        mock_vosk.KaldiRecognizer.return_value = mock_recognizer

        with patch.dict("sys.modules", {"vosk": mock_vosk}):
            rec = plugin._initialize_recognizer()
            assert rec == mock_recognizer
            mock_vosk.Model.assert_called_once_with("/path/to/model")

    def test_execute_success(self):
        """Test successful execution."""
        plugin = TalkPlugin()
        mock_client = Mock()
        args = Namespace(voice=False)

        with patch.object(plugin, "_check_dependencies"):
            with patch.object(plugin, "_initialize_recognizer") as mock_init:
                with patch.object(plugin, "_listen_and_process") as mock_listen:
                    mock_rec = Mock()
                    mock_init.return_value = mock_rec

                    result = plugin.execute(mock_client, args)

                    assert result is True
                    mock_listen.assert_called_once_with(mock_client, mock_rec, False)

    def test_execute_talk_error(self):
        """Test execution when TalkError is raised."""
        plugin = TalkPlugin()
        mock_client = Mock()
        args = Namespace(voice=False)

        with patch.object(plugin, "_check_dependencies", side_effect=TalkError("Failed")):
            with pytest.raises(TalkError):
                plugin.execute(mock_client, args)

    def test_listen_and_process_stop_command(self):
        """Test listening stops on 'stop' command."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_rec = Mock()
        mock_rec.AcceptWaveform.return_value = True
        mock_rec.Result.return_value = json.dumps({"text": "stop"})

        mock_q = Mock()
        mock_q.get.return_value = b"audio data"
        mock_q.empty.return_value = True

        mock_stream = MagicMock()
        mock_sounddevice = MagicMock()
        mock_sounddevice.RawInputStream.return_value.__enter__.return_value = mock_stream

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            with patch("jira_creator.plugins.talk_plugin.queue.Queue", return_value=mock_q):
                plugin._listen_and_process(mock_client, mock_rec, False)
                mock_rec.AcceptWaveform.assert_called()

    def test_listen_and_process_empty_text(self):
        """Test listening handles empty text."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_rec = Mock()
        results = [json.dumps({"text": ""}), json.dumps({"text": "stop"})]
        mock_rec.AcceptWaveform.return_value = True
        mock_rec.Result.side_effect = results

        mock_q = Mock()
        mock_q.get.return_value = b"audio data"
        mock_q.empty.return_value = True

        mock_stream = MagicMock()
        mock_sounddevice = MagicMock()
        mock_sounddevice.RawInputStream.return_value.__enter__.return_value = mock_stream

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            with patch("jira_creator.plugins.talk_plugin.queue.Queue", return_value=mock_q):
                plugin._listen_and_process(mock_client, mock_rec, False)

    def test_listen_and_process_short_command(self):
        """Test listening handles short commands."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_rec = Mock()
        results = [json.dumps({"text": "hi"}), json.dumps({"text": "stop"})]
        mock_rec.AcceptWaveform.return_value = True
        mock_rec.Result.side_effect = results

        mock_q = Mock()
        mock_q.get.return_value = b"audio data"
        mock_q.empty.return_value = True

        mock_stream = MagicMock()
        mock_sounddevice = MagicMock()
        mock_sounddevice.RawInputStream.return_value.__enter__.return_value = mock_stream

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            with patch("jira_creator.plugins.talk_plugin.queue.Queue", return_value=mock_q):
                plugin._listen_and_process(mock_client, mock_rec, False)

    def test_listen_and_process_with_ai_helper(self):
        """Test listening calls AI helper."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_rec = Mock()
        results = [json.dumps({"text": "add issue four three two one to sprint"}), json.dumps({"text": "stop"})]
        mock_rec.AcceptWaveform.return_value = True
        mock_rec.Result.side_effect = results

        mock_q = Mock()
        mock_q.get.return_value = b"audio data"
        mock_q.empty.return_value = True

        mock_stream = MagicMock()
        mock_sounddevice = MagicMock()
        mock_sounddevice.RawInputStream.return_value.__enter__.return_value = mock_stream

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            with patch("jira_creator.plugins.talk_plugin.queue.Queue", return_value=mock_q):
                with patch.object(plugin, "_call_ai_helper") as mock_ai_helper:
                    with patch.object(plugin, "_normalize_issue_references", return_value="normalized text"):
                        plugin._listen_and_process(mock_client, mock_rec, False)
                        mock_ai_helper.assert_called_once()

    def test_listen_and_process_no_waveform(self):
        """Test listening when AcceptWaveform returns False."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_rec = Mock()
        accept_returns = [False, False, True]
        mock_rec.AcceptWaveform.side_effect = accept_returns
        mock_rec.Result.return_value = json.dumps({"text": "stop"})

        mock_q = Mock()
        mock_q.get.return_value = b"audio data"
        mock_q.empty.return_value = True

        mock_stream = MagicMock()
        mock_sounddevice = MagicMock()
        mock_sounddevice.RawInputStream.return_value.__enter__.return_value = mock_stream

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            with patch("jira_creator.plugins.talk_plugin.queue.Queue", return_value=mock_q):
                plugin._listen_and_process(mock_client, mock_rec, False)

    def test_listen_and_process_queue_cleanup(self):
        """Test queue cleanup during listening."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_rec = Mock()
        # First call processes a command, second call returns stop
        mock_rec.AcceptWaveform.side_effect = [True, True]
        mock_rec.Result.side_effect = [
            json.dumps({"text": "add issue one to sprint"}),
            json.dumps({"text": "stop"}),
        ]

        mock_q = Mock()
        mock_q.get.return_value = b"audio data"
        # First two empties are False (for queue cleanup), then True, False, True (for second iteration)
        mock_q.empty.side_effect = [False, True, False, True]
        mock_q.get_nowait.side_effect = [b"old data"]

        mock_stream = MagicMock()
        mock_sounddevice = MagicMock()
        mock_sounddevice.RawInputStream.return_value.__enter__.return_value = mock_stream

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            with patch("jira_creator.plugins.talk_plugin.queue.Queue", return_value=mock_q):
                with patch.object(plugin, "_call_ai_helper"):
                    with patch.object(plugin, "_normalize_issue_references", return_value="normalized text"):
                        plugin._listen_and_process(mock_client, mock_rec, False)
                        assert mock_q.get_nowait.call_count >= 1

    @patch("jira_creator.plugins.talk_plugin.EnvFetcher")
    def test_normalize_issue_references(self, mock_env):
        """Test issue reference normalization."""
        plugin = TalkPlugin()
        mock_env.get.return_value = "AAP"

        mock_w2n = Mock()
        mock_w2n.word_to_num.side_effect = lambda x: {"four": 4, "three": 3, "two": 2, "one": 1}.get(x, x)

        with patch.dict("sys.modules", {"word2number": Mock(w2n=mock_w2n)}):
            text = "add issue four three two one to sprint"
            result = plugin._normalize_issue_references(text)

            assert "AAP-4321" in result

    @patch("jira_creator.plugins.talk_plugin.EnvFetcher")
    def test_normalize_issue_references_no_digits(self, mock_env):
        """Test normalization without digits."""
        plugin = TalkPlugin()
        mock_env.get.return_value = "AAP"

        mock_w2n = Mock()

        with patch.dict("sys.modules", {"word2number": Mock(w2n=mock_w2n)}):
            text = "create a new issue"
            result = plugin._normalize_issue_references(text)

            assert "create a new issue" in result

    def test_fuzzy_digit_cleanup(self):
        """Test fuzzy digit cleanup."""
        plugin = TalkPlugin()

        text = "for free won to"
        result = plugin._fuzzy_digit_cleanup(text)

        assert "four" in result
        assert "three" in result
        assert "one" in result
        assert "two" in result

    def test_word_digits_to_numbers(self):
        """Test word to number conversion."""
        plugin = TalkPlugin()

        mock_w2n = Mock()
        mock_w2n.word_to_num.side_effect = lambda x: {"four": 4, "three": 3}.get(x, x)

        text = "four three"
        result = plugin._word_digits_to_numbers(text, mock_w2n)

        assert "4" in result
        assert "3" in result

    def test_word_digits_to_numbers_value_error(self):
        """Test word to number conversion with ValueError."""
        plugin = TalkPlugin()

        mock_w2n = Mock()
        mock_w2n.word_to_num.side_effect = ValueError("Cannot convert")

        text = "four"
        result = plugin._word_digits_to_numbers(text, mock_w2n)

        # Should handle error gracefully
        assert "four" in result

    def test_word_digits_to_numbers_non_digit_words(self):
        """Test word to number with non-digit words."""
        plugin = TalkPlugin()

        mock_w2n = Mock()

        text = "hello world"
        result = plugin._word_digits_to_numbers(text, mock_w2n)

        assert result == "hello world"

    def test_call_ai_helper_success(self):
        """Test calling AI helper successfully."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_ai_helper = Mock()
        mock_ai_helper.execute.return_value = True
        mock_registry.get_plugin.return_value = mock_ai_helper

        mock_plugin_registry = Mock(return_value=mock_registry)

        with patch.dict(
            "sys.modules", {"jira_creator.core.plugin_registry": Mock(PluginRegistry=mock_plugin_registry)}
        ):
            plugin._call_ai_helper(mock_client, "test command", False)
            mock_ai_helper.execute.assert_called_once()

    def test_call_ai_helper_not_found(self):
        """Test calling AI helper when not found."""
        plugin = TalkPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_registry.get_plugin.return_value = None

        mock_plugin_registry = Mock(return_value=mock_registry)

        with patch.dict(
            "sys.modules", {"jira_creator.core.plugin_registry": Mock(PluginRegistry=mock_plugin_registry)}
        ):
            plugin._call_ai_helper(mock_client, "test command", False)

    def test_call_ai_helper_with_errors(self):
        """Test calling AI helper with various errors."""
        plugin = TalkPlugin()
        mock_client = Mock()

        errors = [ValueError("error"), KeyError("key"), AttributeError("attr")]

        for error in errors:
            mock_registry = Mock()
            mock_ai_helper = Mock()
            mock_ai_helper.execute.side_effect = error
            mock_registry.get_plugin.return_value = mock_ai_helper

            mock_plugin_registry = Mock(return_value=mock_registry)

            with patch.dict(
                "sys.modules", {"jira_creator.core.plugin_registry": Mock(PluginRegistry=mock_plugin_registry)}
            ):
                plugin._call_ai_helper(mock_client, "test command", False)
