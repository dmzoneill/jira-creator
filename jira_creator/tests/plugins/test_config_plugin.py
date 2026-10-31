"""Tests for the config plugin.

Profiles are stored in a real profiles.json under a temporary JIRA_CONFIG_DIR,
and every operation goes through the public execute() / get_profile_setting()
entry points.
"""

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.config_plugin import ConfigError, ConfigPlugin, get_profile_setting

ENV_GET = "jira_creator.plugins.config_plugin.EnvFetcher.get"


def set_args(name="test-profile", **settings):
    """Namespace for `config set-profile` with unset options as None."""
    fields = ("epic", "project", "component", "priority", "story_points_field", "epic_field")
    values = {field: settings.get(field) for field in fields}
    return Namespace(config_action="set-profile", profile_name=name, **values)


@pytest.fixture(name="config_dir")
def fixture_config_dir(tmp_path):
    """Point JIRA_CONFIG_DIR at a fresh temporary directory."""
    with patch(ENV_GET, return_value=str(tmp_path)):
        yield tmp_path


@pytest.fixture(name="write_profiles")
def fixture_write_profiles(config_dir):
    """Write a profiles dict to the temporary profiles.json."""

    def write(profiles):
        (config_dir / "profiles.json").write_text(json.dumps(profiles), encoding="utf-8")

    return write


def read_profiles(config_dir):
    """Profiles currently stored in the temporary profiles.json."""
    return json.loads((config_dir / "profiles.json").read_text(encoding="utf-8"))


class TestConfigPluginBasics:
    """Plugin metadata, argument registration and config file location."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ConfigPlugin()
        assert plugin.command_name == "config"
        assert "configuration" in plugin.help_text.lower()

    def test_register_arguments(self):
        """Test argument registration."""
        mock_parser = Mock(spec=ArgumentParser)
        mock_subparsers = Mock()
        mock_parser.add_subparsers.return_value = mock_subparsers

        ConfigPlugin().register_arguments(mock_parser)

        mock_parser.add_subparsers.assert_called_once()
        assert mock_subparsers.add_parser.call_count == 4  # set, get, list, delete

    def test_rest_operation(self):
        """Test that REST operation returns empty dict."""
        result = ConfigPlugin().rest_operation(Mock())
        assert isinstance(result, dict) and not result

    def test_default_config_dir_is_under_home(self, tmp_path):
        """Without JIRA_CONFIG_DIR, profiles are saved in ~/.jira-creator/profiles.json."""
        with patch(ENV_GET, return_value=""), patch.object(Path, "home", return_value=tmp_path):
            ConfigPlugin().execute(None, set_args(epic="EPIC-1"))

        assert read_profiles(tmp_path / ".jira-creator") == {"test-profile": {"epic": "EPIC-1"}}

    def test_custom_config_dir_is_created(self, tmp_path):
        """JIRA_CONFIG_DIR is used, and created when missing."""
        custom = tmp_path / "custom" / "config"
        with patch(ENV_GET, return_value=str(custom)):
            ConfigPlugin().execute(None, set_args(epic="EPIC-1"))

        assert read_profiles(custom) == {"test-profile": {"epic": "EPIC-1"}}

    def test_unknown_action(self, config_dir, capsys):
        """An unknown action raises ConfigError and prints the failure."""
        assert config_dir.exists()
        with pytest.raises(ConfigError, match="Unknown config action: bogus"):
            ConfigPlugin().execute(None, Namespace(config_action="bogus"))

        assert "❌ Config operation failed" in capsys.readouterr().out


class TestSetProfile:
    """config set-profile."""

    def test_set_profile_success(self, config_dir, capsys):
        """Test setting a profile successfully."""
        args = set_args(epic="EPIC-123", project="AAP", component="analytics", priority="High")

        assert ConfigPlugin().execute(None, args) is True

        assert read_profiles(config_dir)["test-profile"] == {
            "epic": "EPIC-123",
            "project": "AAP",
            "component": "analytics",
            "priority": "High",
        }
        out = capsys.readouterr().out
        assert "✅ Profile 'test-profile' saved successfully" in out
        assert str(config_dir / "profiles.json") in out

    def test_set_profile_with_custom_fields(self, config_dir):
        """story_points_field and epic_field are saved too."""
        args = set_args(epic="EPIC-123", story_points_field="customfield_12345", epic_field="customfield_67890")

        ConfigPlugin().execute(None, args)

        saved = read_profiles(config_dir)["test-profile"]
        assert saved["story_points_field"] == "customfield_12345"
        assert saved["epic_field"] == "customfield_67890"

    def test_set_profile_keeps_other_profiles(self, config_dir, write_profiles):
        """Setting one profile leaves existing ones in place."""
        write_profiles({"other": {"epic": "EPIC-9"}})

        ConfigPlugin().execute(None, set_args(project="AAP"))

        assert read_profiles(config_dir) == {"other": {"epic": "EPIC-9"}, "test-profile": {"project": "AAP"}}

    def test_set_profile_no_settings(self, config_dir):
        """Test setting a profile with no settings provided."""
        with pytest.raises(ConfigError, match="No profile settings provided"):
            ConfigPlugin().execute(None, set_args())

        assert not (config_dir / "profiles.json").exists()


class TestReadAndDeleteProfiles:
    """config get-profile, list-profiles and delete-profile."""

    def test_get_profile_text_output(self, write_profiles, capsys):
        """Test getting profile with text output."""
        write_profiles({"test-profile": {"epic": "EPIC-123", "project": "AAP"}})

        args = Namespace(config_action="get-profile", profile_name="test-profile", output="text")
        assert ConfigPlugin().execute(None, args) is True

        out = capsys.readouterr().out
        assert "📋 Profile: test-profile" in out
        assert "epic: EPIC-123" in out
        assert "project: AAP" in out

    def test_get_profile_json_output(self, write_profiles, capsys):
        """Test getting profile with JSON output."""
        write_profiles({"test-profile": {"epic": "EPIC-123", "project": "AAP"}})

        args = Namespace(config_action="get-profile", profile_name="test-profile", output="json")
        assert ConfigPlugin().execute(None, args) is True

        assert json.loads(capsys.readouterr().out) == {"epic": "EPIC-123", "project": "AAP"}

    def test_get_profile_not_found(self, config_dir):
        """Test getting a non-existent profile."""
        assert config_dir.exists()
        args = Namespace(config_action="get-profile", profile_name="nonexistent", output="text")
        with pytest.raises(ConfigError, match="Profile 'nonexistent' not found"):
            ConfigPlugin().execute(None, args)

    def test_list_profiles_empty(self, config_dir, capsys):
        """Test listing profiles when none exist."""
        assert config_dir.exists()
        assert ConfigPlugin().execute(None, Namespace(config_action="list-profiles")) is True

        assert "No configuration profiles found" in capsys.readouterr().out

    def test_list_profiles_with_data(self, write_profiles, capsys):
        """Test listing profiles with data, sorted by name."""
        write_profiles({"profile2": {"project": "AAP"}, "profile1": {"epic": "EPIC-123"}})

        assert ConfigPlugin().execute(None, Namespace(config_action="list-profiles")) is True

        out = capsys.readouterr().out
        assert out.index("• profile1") < out.index("• profile2")
        assert "epic: EPIC-123" in out

    def test_delete_profile_success(self, config_dir, write_profiles, capsys):
        """Test deleting a profile successfully."""
        write_profiles({"test-profile": {"epic": "EPIC-123"}, "keep": {"epic": "EPIC-1"}})

        args = Namespace(config_action="delete-profile", profile_name="test-profile")
        assert ConfigPlugin().execute(None, args) is True

        assert read_profiles(config_dir) == {"keep": {"epic": "EPIC-1"}}
        assert "✅ Profile 'test-profile' deleted successfully" in capsys.readouterr().out

    def test_delete_profile_not_found(self, config_dir):
        """Test deleting a non-existent profile."""
        assert config_dir.exists()
        args = Namespace(config_action="delete-profile", profile_name="nonexistent")
        with pytest.raises(ConfigError, match="Profile 'nonexistent' not found"):
            ConfigPlugin().execute(None, args)


class TestConfigFileErrors:
    """Unreadable or unwritable profiles.json."""

    def test_load_profiles_json_error(self, config_dir):
        """Invalid JSON in profiles.json raises ConfigError."""
        (config_dir / "profiles.json").write_text("invalid json", encoding="utf-8")
        with pytest.raises(ConfigError, match="Failed to load configuration"):
            ConfigPlugin().execute(None, Namespace(config_action="list-profiles"))

    def test_load_profiles_os_error(self, config_dir):
        """An unreadable profiles.json raises ConfigError."""
        (config_dir / "profiles.json").mkdir()
        with pytest.raises(ConfigError, match="Failed to load configuration"):
            ConfigPlugin().execute(None, Namespace(config_action="list-profiles"))

    def test_save_profiles_io_error(self, config_dir):
        """A failed write raises ConfigError."""
        assert config_dir.exists()
        with (
            patch("builtins.open", side_effect=OSError("Permission denied")),
            pytest.raises(ConfigError, match="Failed to save configuration"),
        ):
            ConfigPlugin().execute(None, set_args(epic="EPIC-123"))


class TestGetProfileSetting:
    """get_profile_setting() helper."""

    def test_get_profile_setting_exists(self, write_profiles):
        """Test getting a setting from a profile."""
        write_profiles({"test-profile": {"epic": "EPIC-123", "project": "AAP"}})
        assert get_profile_setting("test-profile", "epic") == "EPIC-123"

    def test_get_profile_setting_not_exists(self, write_profiles):
        """Test getting a non-existent setting from a profile."""
        write_profiles({"test-profile": {"epic": "EPIC-123"}})
        assert get_profile_setting("test-profile", "component", default="default-component") == "default-component"

    def test_get_profile_setting_profile_not_found(self, config_dir):
        """Test getting a setting when profile doesn't exist."""
        assert config_dir.exists()
        assert get_profile_setting("nonexistent", "epic", default="DEFAULT") == "DEFAULT"
