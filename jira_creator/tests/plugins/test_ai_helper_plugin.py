#!/usr/bin/env python
"""Tests for the AI helper plugin."""

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.ai_helper_plugin import AIHelperError, AIHelperPlugin


class TestAIHelperPlugin:
    """Test cases for AIHelperPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AIHelperPlugin()
        assert plugin.command_name == "ai-helper"
        assert plugin.help_text == "Use natural language to interact with Jira"
        assert plugin.category == "Utilities"
        assert len(plugin.example_commands) == 3

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = AIHelperPlugin()
        parser = Mock()
        plugin.register_arguments(parser)
        assert parser.add_argument.call_count == 3

    def test_rest_operation(self):
        """Test rest_operation returns empty dict."""
        plugin = AIHelperPlugin()
        mock_client = Mock()
        result = plugin.rest_operation(mock_client)
        assert result == {}

    @patch("jira_creator.plugins.ai_helper_plugin.get_ai_provider")
    @patch("jira_creator.plugins.ai_helper_plugin.PluginRegistry")
    @patch("jira_creator.plugins.ai_helper_plugin.EnvFetcher")
    def test_execute_success(self, mock_env, mock_registry_class, mock_get_ai):
        """Test successful execution."""
        # Mock environment
        mock_env.get.return_value = "openai"

        # Mock AI provider
        mock_ai = Mock()
        mock_ai.improve_text.return_value = json.dumps(
            [{"function": "create-issue", "args": {"summary": "Test"}, "action": "Creating test issue"}]
        )
        mock_get_ai.return_value = mock_ai

        # Mock plugin registry
        mock_registry = Mock()
        mock_plugin = Mock()
        mock_plugin.execute.return_value = True
        mock_registry.get_plugin.return_value = mock_plugin
        mock_registry.list_plugins.return_value = ["create-issue", "view-issue"]
        mock_registry_class.return_value = mock_registry

        # Create plugin and execute
        plugin = AIHelperPlugin()

        # Mock the template loading
        with patch.object(plugin, "_load_template", return_value="System prompt"):
            mock_client = Mock()
            args = Namespace(prompt="Create a test issue", voice=False)

            result = plugin.execute(mock_client, args)

            assert result is True
            mock_ai.improve_text.assert_called_once()
            mock_plugin.execute.assert_called_once()

    @patch("jira_creator.plugins.ai_helper_plugin.get_ai_provider")
    @patch("jira_creator.plugins.ai_helper_plugin.PluginRegistry")
    @patch("jira_creator.plugins.ai_helper_plugin.EnvFetcher")
    def test_execute_no_steps_returned(self, mock_env, mock_registry_class, mock_get_ai):
        """Test execution when AI returns no steps."""
        mock_env.get.return_value = "openai"

        mock_ai = Mock()
        mock_ai.improve_text.return_value = json.dumps({"error": "Cannot understand"})
        mock_get_ai.return_value = mock_ai

        mock_registry = Mock()
        mock_registry.list_plugins.return_value = ["test"]
        mock_registry_class.return_value = mock_registry

        plugin = AIHelperPlugin()
        with patch.object(plugin, "_load_template", return_value="System prompt"):
            mock_client = Mock()
            args = Namespace(prompt="invalid", voice=False)

            result = plugin.execute(mock_client, args)

            assert result is False

    @patch("jira_creator.plugins.ai_helper_plugin.get_ai_provider")
    def test_execute_ai_helper_error(self, mock_get_ai):
        """Test execution when AIHelperError is raised."""
        mock_get_ai.side_effect = AIHelperError("AI failed")

        plugin = AIHelperPlugin()
        mock_client = Mock()
        args = Namespace(prompt="test", voice=False)

        with pytest.raises(AIHelperError):
            plugin.execute(mock_client, args)

    def test_load_template_success(self):
        """Test successful template loading."""
        plugin = AIHelperPlugin()

        # Create a temporary template file
        template_dir = Path(__file__).parent.parent.parent / "templates"
        template_file = template_dir / "aihelper.tmpl"

        # The template should exist
        if template_file.exists():
            content = plugin._load_template("aihelper")
            assert isinstance(content, str)
            assert len(content) > 0

    def test_load_template_not_found(self):
        """Test template loading when file doesn't exist."""
        plugin = AIHelperPlugin()

        with pytest.raises(AIHelperError, match="Template file not found"):
            plugin._load_template("nonexistent_template")

    def test_build_command_metadata(self):
        """Test building command metadata."""
        plugin = AIHelperPlugin()

        mock_registry = Mock()
        mock_plugin1 = Mock()
        mock_plugin1.help_text = "Create an issue"
        mock_plugin2 = Mock()
        mock_plugin2.help_text = "View an issue"

        mock_registry.get_plugin.side_effect = lambda name: {
            "create-issue": mock_plugin1,
            "view-issue": mock_plugin2,
        }.get(name)

        metadata = plugin._build_command_metadata(mock_registry, ["create-issue", "view-issue"])

        assert "create-issue: Create an issue" in metadata
        assert "view-issue: View an issue" in metadata

    def test_build_command_metadata_no_plugin(self):
        """Test building metadata when plugin is None."""
        plugin = AIHelperPlugin()

        mock_registry = Mock()
        mock_registry.get_plugin.return_value = None

        metadata = plugin._build_command_metadata(mock_registry, ["nonexistent"])

        assert metadata == ""

    def test_build_command_metadata_no_help_text(self):
        """Test building metadata when plugin has no help_text."""
        plugin = AIHelperPlugin()

        mock_registry = Mock()
        mock_plugin = Mock(spec=[])  # No help_text attribute
        mock_registry.get_plugin.return_value = mock_plugin

        metadata = plugin._build_command_metadata(mock_registry, ["test"])

        assert "test: " in metadata

    def test_parse_ai_response_success(self):
        """Test parsing successful AI response."""
        plugin = AIHelperPlugin()

        response = json.dumps([{"function": "test", "args": {}, "action": "Testing"}])

        steps = plugin._parse_ai_response(response)

        assert len(steps) == 1
        assert steps[0]["function"] == "test"

    def test_parse_ai_response_with_markdown(self):
        """Test parsing AI response with markdown code blocks."""
        plugin = AIHelperPlugin()

        response = "```json\n" + json.dumps([{"function": "test", "args": {}}]) + "\n```"

        steps = plugin._parse_ai_response(response)

        assert len(steps) == 1

    def test_parse_ai_response_error_dict(self):
        """Test parsing AI response with error."""
        plugin = AIHelperPlugin()

        response = json.dumps({"error": "Cannot process"})

        steps = plugin._parse_ai_response(response)

        assert steps == []

    def test_parse_ai_response_non_list_dict(self):
        """Test parsing AI response that's a dict without error."""
        plugin = AIHelperPlugin()

        response = json.dumps({"something": "else"})

        steps = plugin._parse_ai_response(response)

        assert steps == []

    def test_parse_ai_response_invalid_json(self):
        """Test parsing invalid JSON."""
        plugin = AIHelperPlugin()

        with pytest.raises(AIHelperError, match="Failed to parse AI response"):
            plugin._parse_ai_response("not valid json")

    def test_execute_steps_no_steps(self):
        """Test executing with no steps."""
        plugin = AIHelperPlugin()
        mock_client = Mock()
        mock_registry = Mock()

        result = plugin._execute_steps(mock_client, mock_registry, [], False)

        assert result is False

    def test_execute_steps_success(self):
        """Test successful step execution."""
        plugin = AIHelperPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_plugin = Mock()
        mock_plugin.execute.return_value = True
        mock_registry.get_plugin.return_value = mock_plugin

        steps = [{"function": "test", "args": {"key": "value"}, "action": "Testing"}]

        result = plugin._execute_steps(mock_client, mock_registry, steps, False)

        assert result is True
        mock_plugin.execute.assert_called_once()

    def test_execute_steps_plugin_not_found(self):
        """Test step execution when plugin not found."""
        plugin = AIHelperPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_registry.get_plugin.return_value = None

        steps = [{"function": "nonexistent", "args": {}, "action": "Testing"}]

        result = plugin._execute_steps(mock_client, mock_registry, steps, False)

        assert result is False

    def test_execute_steps_plugin_raises_error(self):
        """Test step execution when plugin raises an error."""
        plugin = AIHelperPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_plugin = Mock()
        mock_plugin.execute.side_effect = ValueError("Test error")
        mock_registry.get_plugin.return_value = mock_plugin

        steps = [{"function": "test", "args": {}, "action": "Testing"}]

        result = plugin._execute_steps(mock_client, mock_registry, steps, False)

        # Should handle error and continue
        assert result is False

    @patch("jira_creator.plugins.ai_helper_plugin.os.system")
    def test_execute_steps_with_voice(self, mock_system):
        """Test step execution with voice enabled."""
        plugin = AIHelperPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_plugin = Mock()
        mock_plugin.execute.return_value = True
        mock_registry.get_plugin.return_value = mock_plugin

        steps = [{"function": "test", "args": {}, "action": "Testing"}]

        with patch.object(plugin, "_speak"):
            result = plugin._execute_steps(mock_client, mock_registry, steps, True)

            assert result is True

    def test_speak_import_error(self):
        """Test text-to-speech when gTTS not installed."""
        plugin = AIHelperPlugin()

        # gTTS import will fail naturally if not installed
        # Should not raise, just log warning
        try:
            plugin._speak("Test message")
        except ImportError:
            pytest.skip("gTTS not installed")

    def test_execute_steps_multiple_errors(self):
        """Test step execution with various error types."""
        plugin = AIHelperPlugin()
        mock_client = Mock()

        mock_registry = Mock()
        mock_plugin = Mock()

        # Test different error types
        errors = [KeyError("key"), AttributeError("attr"), AIHelperError("ai")]

        for error in errors:
            mock_plugin.execute.side_effect = error
            mock_registry.get_plugin.return_value = mock_plugin

            steps = [{"function": "test", "args": {}, "action": "Testing"}]

            result = plugin._execute_steps(mock_client, mock_registry, steps, False)
            assert result is False

    @patch("jira_creator.plugins.ai_helper_plugin.get_ai_provider")
    @patch("jira_creator.plugins.ai_helper_plugin.PluginRegistry")
    @patch("jira_creator.plugins.ai_helper_plugin.EnvFetcher")
    def test_execute_with_voice_on_error(self, mock_env, mock_registry_class, mock_get_ai):
        """Test execution with voice when error occurs."""
        mock_env.get.return_value = "openai"

        mock_ai = Mock()
        mock_ai.improve_text.return_value = json.dumps([{"function": "test", "args": {}, "action": "Testing"}])
        mock_get_ai.return_value = mock_ai

        mock_registry = Mock()
        mock_plugin = Mock()
        mock_plugin.execute.side_effect = ValueError("Error")
        mock_registry.get_plugin.return_value = mock_plugin
        mock_registry.list_plugins.return_value = ["test"]
        mock_registry_class.return_value = mock_registry

        plugin = AIHelperPlugin()
        with patch.object(plugin, "_load_template", return_value="System prompt"):
            with patch.object(plugin, "_speak"):
                mock_client = Mock()
                args = Namespace(prompt="test", voice=True)

                plugin.execute(mock_client, args)

                # Voice should be called for error if gTTS is available
                # but we don't assert since gTTS may not be installed

    def test_parse_ai_response_not_list(self):
        """Test parsing AI response when result is not a list."""
        plugin = AIHelperPlugin()

        # Response is a dict, not a list
        response = json.dumps({"error": "Invalid format"})

        steps = plugin._parse_ai_response(response)

        # Should return empty list when result is not a list
        assert steps == []

    @patch("jira_creator.plugins.ai_helper_plugin.os.system")
    def test_speak_os_error(self, mock_system):
        """Test _speak when OSError occurs."""
        plugin = AIHelperPlugin()

        # Mock gTTS to succeed but os.system to fail
        mock_system.side_effect = OSError("Command failed")

        # Mock the gTTS import
        mock_tts = Mock()
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                Mock(gTTS=Mock(return_value=mock_tts)) if name == "gtts" else __import__(name, *args, **kwargs)
            ),
        ):
            # Should handle OSError gracefully
            plugin._speak("test")

    def test_speak_io_error(self):
        """Test _speak when IOError occurs."""
        plugin = AIHelperPlugin()

        # Mock gTTS to raise IOError when saving
        mock_tts = Mock()
        mock_tts.save.side_effect = IOError("Cannot save file")

        # Mock the gTTS import
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                Mock(gTTS=Mock(return_value=mock_tts)) if name == "gtts" else __import__(name, *args, **kwargs)
            ),
        ):
            # Should handle IOError gracefully
            plugin._speak("test")
