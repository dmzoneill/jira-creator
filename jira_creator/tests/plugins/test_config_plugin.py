#!/usr/bin/env python
"""Tests for the config plugin."""

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import ConfigError
from jira_creator.plugins.config_plugin import ConfigPlugin, get_profile_setting

# Add JIRA_CONFIG_DIR to EnvFetcher vars for testing
if not hasattr(EnvFetcher, "vars") or "JIRA_CONFIG_DIR" not in EnvFetcher.vars:
    if not hasattr(EnvFetcher, "vars"):
        EnvFetcher.vars = {}
    EnvFetcher.vars["JIRA_CONFIG_DIR"] = None


class TestConfigPlugin:
    """Test cases for ConfigPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ConfigPlugin()
        assert plugin.command_name == "config"
        assert "configuration" in plugin.help_text.lower()

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ConfigPlugin()
        mock_parser = Mock(spec=ArgumentParser)
        mock_subparsers = Mock()
        mock_parser.add_subparsers.return_value = mock_subparsers

        plugin.register_arguments(mock_parser)

        # Verify subparsers was created
        mock_parser.add_subparsers.assert_called_once()
        # Verify subcommands were added
        assert mock_subparsers.add_parser.call_count == 4  # set, get, list, delete

    def test_rest_operation(self):
        """Test that REST operation returns empty dict."""
        plugin = ConfigPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client)

        assert result == {}

    def test_get_config_file_default(self):
        """Test getting default config file path."""
        plugin = ConfigPlugin()

        with patch("jira_creator.plugins.config_plugin.EnvFetcher.get", return_value=""):
            result = plugin._get_config_file()  # pylint: disable=protected-access

            # Verify it returns a Path ending with profiles.json
            assert str(result).endswith("profiles.json")
            assert ".jira-creator" in str(result)

    @patch("jira_creator.plugins.config_plugin.Path")
    def test_get_config_file_custom(self, mock_path):
        """Test getting custom config file path."""
        plugin = ConfigPlugin()

        with patch("jira_creator.plugins.config_plugin.EnvFetcher.get", return_value="/custom/config"):
            plugin._get_config_file()  # pylint: disable=protected-access

            mock_path.assert_called_with("/custom/config")

    def test_load_profiles_file_not_exists(self):
        """Test loading profiles when file doesn't exist."""
        plugin = ConfigPlugin()

        with patch.object(plugin, "_get_config_file") as mock_get_file:
            mock_file = Mock()
            mock_file.exists.return_value = False
            mock_get_file.return_value = mock_file

            result = plugin._load_profiles()  # pylint: disable=protected-access

        assert result == {}

    def test_load_profiles_success(self):
        """Test loading profiles successfully."""
        plugin = ConfigPlugin()
        profiles_data = {"profile1": {"epic": "EPIC-123"}}

        with patch.object(plugin, "_get_config_file") as mock_get_file:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_get_file.return_value = mock_file

            with patch("builtins.open", mock_open(read_data=json.dumps(profiles_data))):
                result = plugin._load_profiles()  # pylint: disable=protected-access

        assert result == profiles_data

    def test_load_profiles_json_error(self):
        """Test loading profiles with JSON decode error."""
        plugin = ConfigPlugin()

        with patch.object(plugin, "_get_config_file") as mock_get_file:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_get_file.return_value = mock_file

            with patch("builtins.open", mock_open(read_data="invalid json")):
                with pytest.raises(ConfigError, match="Failed to load configuration"):
                    plugin._load_profiles()  # pylint: disable=protected-access

    def test_save_profiles_success(self):
        """Test saving profiles successfully."""
        plugin = ConfigPlugin()
        profiles = {"profile1": {"epic": "EPIC-123"}}

        mock_file = mock_open()
        with patch.object(plugin, "_get_config_file") as mock_get_file:
            mock_get_file.return_value = Path("/test/profiles.json")

            with patch("builtins.open", mock_file):
                plugin._save_profiles(profiles)  # pylint: disable=protected-access

        # Verify file was written
        mock_file.assert_called_once()

    def test_save_profiles_io_error(self):
        """Test saving profiles with IO error."""
        plugin = ConfigPlugin()
        profiles = {"profile1": {"epic": "EPIC-123"}}

        with patch.object(plugin, "_get_config_file") as mock_get_file:
            mock_get_file.return_value = Path("/test/profiles.json")

            with patch("builtins.open", side_effect=OSError("Permission denied")):
                with pytest.raises(ConfigError, match="Failed to save configuration"):
                    plugin._save_profiles(profiles)  # pylint: disable=protected-access

    @patch("builtins.print")
    def test_set_profile_success(self, mock_print):
        """Test setting a profile successfully."""
        plugin = ConfigPlugin()

        args = Namespace(
            profile_name="test-profile",
            epic="EPIC-123",
            project="AAP",
            component="analytics",
            priority="High",
            story_points_field=None,
            epic_field=None,
        )

        with patch.object(plugin, "_get_config_file", return_value=Path("/test/profiles.json")):
            with patch.object(plugin, "_load_profiles", return_value={}):
                with patch.object(plugin, "_save_profiles") as mock_save:
                    result = plugin._set_profile(args)  # pylint: disable=protected-access

        assert result is True
        mock_save.assert_called_once()
        saved_profiles = mock_save.call_args[0][0]
        assert "test-profile" in saved_profiles
        assert saved_profiles["test-profile"]["epic"] == "EPIC-123"
        assert saved_profiles["test-profile"]["project"] == "AAP"

    @patch("builtins.print")
    def test_set_profile_no_settings(self, mock_print):
        """Test setting a profile with no settings provided."""
        plugin = ConfigPlugin()

        args = Namespace(
            profile_name="test-profile",
            epic=None,
            project=None,
            component=None,
            priority=None,
            story_points_field=None,
            epic_field=None,
        )

        with patch.object(plugin, "_load_profiles", return_value={}):
            with pytest.raises(ConfigError, match="No profile settings provided"):
                plugin._set_profile(args)  # pylint: disable=protected-access

    @patch("builtins.print")
    def test_get_profile_text_output(self, mock_print):
        """Test getting a profile with text output."""
        plugin = ConfigPlugin()

        profiles = {"test-profile": {"epic": "EPIC-123", "project": "AAP"}}

        with patch.object(plugin, "_load_profiles", return_value=profiles):
            args = Namespace(profile_name="test-profile", output="text")
            result = plugin._get_profile(args)  # pylint: disable=protected-access

        assert result is True
        assert mock_print.called

    @patch("builtins.print")
    def test_get_profile_json_output(self, mock_print):
        """Test getting a profile with JSON output."""
        plugin = ConfigPlugin()

        profiles = {"test-profile": {"epic": "EPIC-123", "project": "AAP"}}

        with patch.object(plugin, "_load_profiles", return_value=profiles):
            args = Namespace(profile_name="test-profile", output="json")
            result = plugin._get_profile(args)  # pylint: disable=protected-access

        assert result is True
        assert mock_print.called
        # Verify JSON was printed
        call_args = str(mock_print.call_args_list[0])
        assert "EPIC-123" in call_args

    def test_get_profile_not_found(self):
        """Test getting a non-existent profile."""
        plugin = ConfigPlugin()

        with patch.object(plugin, "_load_profiles", return_value={}):
            args = Namespace(profile_name="nonexistent", output="text")

            with pytest.raises(ConfigError, match="Profile 'nonexistent' not found"):
                plugin._get_profile(args)  # pylint: disable=protected-access

    @patch("builtins.print")
    def test_list_profiles_empty(self, mock_print):
        """Test listing profiles when none exist."""
        plugin = ConfigPlugin()

        with patch.object(plugin, "_load_profiles", return_value={}):
            result = plugin._list_profiles()  # pylint: disable=protected-access

        assert result is True
        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("No configuration profiles" in call for call in print_calls)

    @patch("builtins.print")
    def test_list_profiles_with_data(self, mock_print):
        """Test listing profiles with existing data."""
        plugin = ConfigPlugin()

        profiles = {"profile1": {"epic": "EPIC-123"}, "profile2": {"project": "AAP"}}

        with patch.object(plugin, "_load_profiles", return_value=profiles):
            result = plugin._list_profiles()  # pylint: disable=protected-access

        assert result is True
        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("profile1" in call for call in print_calls)
        assert any("profile2" in call for call in print_calls)

    @patch("builtins.print")
    def test_delete_profile_success(self, mock_print):
        """Test deleting a profile successfully."""
        plugin = ConfigPlugin()

        profiles = {"test-profile": {"epic": "EPIC-123"}}

        with patch.object(plugin, "_load_profiles", return_value=profiles.copy()):
            with patch.object(plugin, "_save_profiles") as mock_save:
                args = Namespace(profile_name="test-profile")
                result = plugin._delete_profile(args)  # pylint: disable=protected-access

        assert result is True
        mock_save.assert_called_once()
        saved_profiles = mock_save.call_args[0][0]
        assert "test-profile" not in saved_profiles

    def test_delete_profile_not_found(self):
        """Test deleting a non-existent profile."""
        plugin = ConfigPlugin()

        with patch.object(plugin, "_load_profiles", return_value={}):
            args = Namespace(profile_name="nonexistent")

            with pytest.raises(ConfigError, match="Profile 'nonexistent' not found"):
                plugin._delete_profile(args)  # pylint: disable=protected-access

    def test_get_profile_setting_exists(self):
        """Test getting a setting from a profile."""
        profiles = {"test-profile": {"epic": "EPIC-123", "project": "AAP"}}

        with patch.object(ConfigPlugin, "_load_profiles", return_value=profiles):
            result = get_profile_setting("test-profile", "epic")

        assert result == "EPIC-123"

    def test_get_profile_setting_not_exists(self):
        """Test getting a non-existent setting from a profile."""
        profiles = {"test-profile": {"epic": "EPIC-123"}}

        with patch.object(ConfigPlugin, "_load_profiles", return_value=profiles):
            result = get_profile_setting("test-profile", "component", default="default-component")

        assert result == "default-component"

    def test_get_profile_setting_profile_not_found(self):
        """Test getting a setting when profile doesn't exist."""
        with patch.object(ConfigPlugin, "_load_profiles", return_value={}):
            result = get_profile_setting("nonexistent", "epic", default="DEFAULT")

        assert result == "DEFAULT"

    @patch("builtins.print")
    def test_execute_set_profile(self, mock_print):
        """Test executing set-profile action."""
        plugin = ConfigPlugin()
        mock_client = Mock()

        args = Namespace(
            config_action="set-profile",
            profile_name="test",
            epic="EPIC-123",
            project=None,
            component=None,
            priority=None,
            story_points_field=None,
            epic_field=None,
        )

        with patch.object(plugin, "_get_config_file", return_value=Path("/test/profiles.json")):
            with patch.object(plugin, "_load_profiles", return_value={}):
                with patch.object(plugin, "_save_profiles"):
                    result = plugin.execute(mock_client, args)

        assert result is True

    def test_execute_unknown_action(self):
        """Test executing an unknown action."""
        plugin = ConfigPlugin()
        mock_client = Mock()

        args = Namespace(config_action="unknown-action")

        with pytest.raises(ConfigError, match="Unknown config action"):
            plugin.execute(mock_client, args)

    @patch("builtins.print")
    def test_execute_get_profile(self, mock_print):
        """Test executing get-profile action - covers line 78."""
        plugin = ConfigPlugin()
        mock_client = Mock()

        profiles = {"test": {"epic": "EPIC-123"}}

        args = Namespace(config_action="get-profile", profile_name="test", output="text")

        with patch.object(plugin, "_load_profiles", return_value=profiles):
            result = plugin.execute(mock_client, args)

        assert result is True

    @patch("builtins.print")
    def test_execute_list_profiles(self, mock_print):
        """Test executing list-profiles action - covers line 80."""
        plugin = ConfigPlugin()
        mock_client = Mock()

        args = Namespace(config_action="list-profiles")

        with patch.object(plugin, "_load_profiles", return_value={}):
            result = plugin.execute(mock_client, args)

        assert result is True

    @patch("builtins.print")
    def test_execute_delete_profile(self, mock_print):
        """Test executing delete-profile action - covers line 82."""
        plugin = ConfigPlugin()
        mock_client = Mock()

        profiles = {"test": {"epic": "EPIC-123"}}

        args = Namespace(config_action="delete-profile", profile_name="test")

        with patch.object(plugin, "_load_profiles", return_value=profiles.copy()):
            with patch.object(plugin, "_save_profiles"):
                result = plugin.execute(mock_client, args)

        assert result is True

    @patch("builtins.print")
    def test_set_profile_with_custom_fields(self, mock_print):
        """Test setting a profile with story_points_field and epic_field - covers lines 116, 118."""
        plugin = ConfigPlugin()

        args = Namespace(
            profile_name="test-profile",
            epic="EPIC-123",
            project="AAP",
            component=None,
            priority=None,
            story_points_field="customfield_12345",
            epic_field="customfield_67890",
        )

        with patch.object(plugin, "_get_config_file", return_value=Path("/test/profiles.json")):
            with patch.object(plugin, "_load_profiles", return_value={}):
                with patch.object(plugin, "_save_profiles") as mock_save:
                    result = plugin._set_profile(args)  # pylint: disable=protected-access

        assert result is True
        saved_profiles = mock_save.call_args[0][0]
        assert saved_profiles["test-profile"]["story_points_field"] == "customfield_12345"
        assert saved_profiles["test-profile"]["epic_field"] == "customfield_67890"
