"""Tests for the AI helper plugin, exercised through its public interface."""

import json
import sys
from argparse import ArgumentParser, Namespace
from contextlib import contextmanager
from unittest.mock import Mock, mock_open, patch

import pytest

from jira_creator.plugins.ai_helper_plugin import AIHelperError, AIHelperPlugin

MODULE = "jira_creator.plugins.ai_helper_plugin"


def make_registry(plugins):
    """Build a mock registry exposing the given name -> plugin mapping."""
    registry = Mock()
    registry.list_plugins.return_value = list(plugins)
    registry.get_plugin.side_effect = plugins.get
    return registry


@contextmanager
def ai_environment(ai_response, registry):
    """Patch the AI provider, environment and registry used by execute()."""
    ai = Mock()
    ai.improve_text.return_value = ai_response
    with (
        patch(f"{MODULE}.get_ai_provider", return_value=ai),
        patch(f"{MODULE}.EnvFetcher"),
        patch(f"{MODULE}.PluginRegistry", return_value=registry),
    ):
        yield ai


def run(ai_response, plugins, voice=False, prompt="do something"):
    """Run the plugin's execute() with a mocked AI response and registry."""
    registry = make_registry(plugins)
    with ai_environment(ai_response, registry) as ai:
        result = AIHelperPlugin().execute(Mock(), Namespace(prompt=prompt, voice=voice))
    return result, ai, registry


def steps_json(*names):
    """Return a JSON list of steps calling the given plugin names."""
    return json.dumps([{"function": n, "args": {}, "action": f"Running {n}"} for n in names])


class TestAIHelperPluginBasics:
    """Plugin properties, arguments and prompt building."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AIHelperPlugin()
        assert plugin.command_name == "ai-helper"
        assert "natural language" in plugin.help_text.lower()
        assert plugin.category == "Utilities"
        assert len(plugin.example_commands) == 3
        assert plugin.get_plugin_exceptions() == {"AIHelperError": AIHelperError}

    def test_register_arguments(self):
        """Test argument registration."""
        parser = ArgumentParser()
        AIHelperPlugin().register_arguments(parser)
        args = parser.parse_args(["hello", "--voice", "--no-ai"])
        assert args.prompt == "hello"
        assert args.voice is True
        assert args.no_ai is True

    def test_rest_operation(self):
        """Test rest_operation returns an empty dict."""
        result = AIHelperPlugin().rest_operation(Mock())
        assert isinstance(result, dict) and not result

    def test_prompt_includes_template_commands_and_request(self):
        """The real template, sorted command metadata and the request reach the AI."""
        create, view = Mock(help_text="Create an issue"), Mock(help_text="View an issue")
        _, ai, _ = run(steps_json("view-issue"), {"view-issue": view, "create-issue": create}, prompt="show AAP-1")
        prompt = ai.improve_text.call_args[0][0]
        assert "Available Commands:\n  - create-issue: Create an issue\n  - view-issue: View an issue" in prompt
        assert prompt.endswith("User Request: show AAP-1")
        assert len(prompt.split("\n\nAvailable Commands:")[0]) > 0

    def test_prompt_skips_missing_plugins_and_missing_help(self):
        """Plugins the registry can't load are skipped; plugins without help_text get an empty description."""
        bare = Mock(spec=["execute"])
        plugins = {"gone": None, "bare": bare}
        _, ai, _ = run(steps_json("bare"), plugins)
        prompt = ai.improve_text.call_args[0][0]
        assert "  - bare: " in prompt
        assert "gone" not in prompt.split("User Request:")[0]

    def test_missing_template_raises(self):
        """A missing template file raises AIHelperError."""
        with (
            patch("builtins.open", side_effect=FileNotFoundError),
            patch(f"{MODULE}.get_ai_provider"),
            patch(f"{MODULE}.EnvFetcher"),
            pytest.raises(AIHelperError, match="Template file not found"),
        ):
            AIHelperPlugin().execute(Mock(), Namespace(prompt="x", voice=False))

    def test_template_content_is_used(self):
        """Template text is placed at the start of the prompt."""
        registry = make_registry({})
        with (
            ai_environment("[]", registry) as ai,
            patch("builtins.open", mock_open(read_data="SYSTEM PROMPT")),
        ):
            AIHelperPlugin().execute(Mock(), Namespace(prompt="x", voice=False))
        assert ai.improve_text.call_args[0][0].startswith("SYSTEM PROMPT\n\nAvailable Commands:")


class TestAIHelperPluginResponses:
    """Parsing of AI responses."""

    def test_plain_json_steps_execute(self):
        """A JSON list of steps is executed."""
        plugin = Mock()
        result, _, _ = run(steps_json("test"), {"test": plugin})
        assert result is True
        plugin.execute.assert_called_once()

    def test_markdown_fenced_json_steps_execute(self):
        """Markdown code fences around the JSON are stripped."""
        plugin = Mock()
        result, _, _ = run("```json\n" + steps_json("test") + "\n```", {"test": plugin})
        assert result is True
        plugin.execute.assert_called_once()

    def test_error_dict_returns_false(self, capsys):
        """An error object from the AI is reported and nothing runs."""
        result, _, _ = run(json.dumps({"error": "Cannot understand"}), {})
        assert result is False
        assert "Cannot understand" in capsys.readouterr().out

    def test_non_error_dict_returns_false(self):
        """A dict without an error key yields no steps."""
        result, _, _ = run(json.dumps({"foo": "bar"}), {})
        assert result is False

    def test_non_list_json_returns_false(self):
        """A JSON scalar yields no steps."""
        result, _, _ = run('"just a string"', {})
        assert result is False

    def test_empty_list_returns_false(self, capsys):
        """An empty step list reports that the request wasn't understood."""
        result, _, _ = run("[]", {})
        assert result is False
        assert "couldn't understand" in capsys.readouterr().out

    def test_invalid_json_raises(self):
        """Invalid JSON raises AIHelperError."""
        with pytest.raises(AIHelperError, match="Failed to parse AI response"):
            run("not valid json", {})


class TestAIHelperPluginSteps:
    """Step execution and text-to-speech."""

    def test_step_args_passed_as_namespace(self):
        """Step args are passed to the plugin as a Namespace."""
        plugin = Mock()
        response = json.dumps([{"function": "test", "args": {"key": "AAP-1"}, "action": "Testing"}])
        run(response, {"test": plugin})
        assert plugin.execute.call_args[0][1] == Namespace(key="AAP-1")

    def test_step_defaults_when_fields_missing(self, capsys):
        """Missing function/args/action fall back to defaults."""
        result, _, _ = run(json.dumps([{}]), {})
        assert result is False
        assert "Executing command" in capsys.readouterr().out

    def test_plugin_not_found_is_skipped(self, capsys):
        """Unknown commands are skipped."""
        result, _, _ = run(steps_json("missing"), {})
        assert result is False
        assert "Command 'missing' not found" in capsys.readouterr().out

    def test_plugin_error_is_reported(self, capsys):
        """A failing step is reported and doesn't stop later steps."""
        bad = Mock()
        bad.execute.side_effect = ValueError("boom")
        good = Mock()
        result, _, _ = run(steps_json("bad", "good"), {"bad": bad, "good": good})
        assert result is True
        out = capsys.readouterr().out
        assert "Failed: boom" in out
        assert "Executed 1 of 2 steps" in out

    def test_all_steps_fail(self):
        """All steps failing returns False."""
        bad = Mock()
        bad.execute.side_effect = KeyError("k")
        result, _, _ = run(steps_json("bad", "bad"), {"bad": bad})
        assert result is False

    def test_voice_plays_audio_for_success_and_failure(self):
        """With --voice, gTTS output is played with mpg123 for each step."""
        bad = Mock()
        bad.execute.side_effect = ValueError("boom")
        gtts = Mock()
        with (
            patch.dict(sys.modules, {"gtts": gtts}),
            patch(f"{MODULE}.subprocess.run") as mock_run,
        ):
            run(steps_json("good", "bad"), {"good": Mock(), "bad": bad}, voice=True)
        spoken = [c.kwargs["text"] for c in gtts.gTTS.call_args_list]
        assert spoken == ["Running good", "Failed: boom"]
        assert mock_run.call_count == 2
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "mpg123" and len(cmd) == 2
        assert mock_run.call_args.kwargs["check"] is False

    def test_voice_without_gtts_is_skipped(self):
        """Missing gTTS is handled gracefully."""
        with (
            patch.dict(sys.modules, {"gtts": None}),
            patch(f"{MODULE}.subprocess.run") as mock_run,
        ):
            result, _, _ = run(steps_json("good"), {"good": Mock()}, voice=True)
        assert result is True
        mock_run.assert_not_called()

    def test_voice_playback_os_error_is_handled(self):
        """An OSError from playback is logged, not raised."""
        with (
            patch.dict(sys.modules, {"gtts": Mock()}),
            patch(f"{MODULE}.subprocess.run", side_effect=OSError("no mpg123")),
        ):
            result, _, _ = run(steps_json("good"), {"good": Mock()}, voice=True)
        assert result is True

    def test_voice_save_error_is_handled(self):
        """An OSError while saving audio is logged, not raised."""
        gtts = Mock()
        gtts.gTTS.return_value.save.side_effect = OSError("disk full")
        with (
            patch.dict(sys.modules, {"gtts": gtts}),
            patch(f"{MODULE}.subprocess.run") as mock_run,
        ):
            result, _, _ = run(steps_json("good"), {"good": Mock()}, voice=True)
        assert result is True
        mock_run.assert_not_called()
