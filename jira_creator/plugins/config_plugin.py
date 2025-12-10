#!/usr/bin/env python
"""
Config plugin for jira-creator.

This plugin implements configuration profile management for storing
commonly used settings (epic, project, component, etc.).
"""

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import ConfigError

logger = get_logger("config")


class ConfigPlugin(JiraPlugin):
    """Plugin for managing configuration profiles."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "config"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Manage configuration profiles for common settings"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Utilities"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["config", "config --show-all"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        subparsers = parser.add_subparsers(dest="config_action", required=True)

        # set-profile subcommand
        set_parser = subparsers.add_parser("set-profile", help="Create or update a configuration profile")
        set_parser.add_argument("profile_name", help="Name of the profile")
        set_parser.add_argument("--epic", help="Epic to link stories to")
        set_parser.add_argument("--project", help="Project key")
        set_parser.add_argument("--component", help="Component name")
        set_parser.add_argument("--priority", help="Priority (e.g., Normal, High)")
        set_parser.add_argument("--story-points-field", help="Custom field ID for story points")
        set_parser.add_argument("--epic-field", help="Custom field ID for epic link")

        # get-profile subcommand
        get_parser = subparsers.add_parser("get-profile", help="Display a configuration profile")
        get_parser.add_argument("profile_name", help="Name of the profile")
        get_parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")

        # list-profiles subcommand
        subparsers.add_parser("list-profiles", help="List all configuration profiles")

        # delete-profile subcommand
        delete_parser = subparsers.add_parser("delete-profile", help="Delete a configuration profile")
        delete_parser.add_argument("profile_name", help="Name of the profile to delete")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the config command.

        Arguments:
            client: JiraClient instance (not used for config)
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        logger.info("Config operation: %s", args.config_action)

        try:
            if args.config_action == "set-profile":
                return self._set_profile(args)
            if args.config_action == "get-profile":
                return self._get_profile(args)
            if args.config_action == "list-profiles":
                return self._list_profiles()
            if args.config_action == "delete-profile":
                return self._delete_profile(args)

            logger.error("Unknown config action: %s", args.config_action)
            raise ConfigError(f"Unknown config action: {args.config_action}")

        except ConfigError as e:
            logger.error("Config operation failed: %s", e)
            print(f"❌ Config operation failed: {e}")
            raise

    def _set_profile(self, args: Namespace) -> bool:
        """
        Create or update a configuration profile.

        Arguments:
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        config_file = self._get_config_file()
        profiles = self._load_profiles()

        # Build profile data from arguments
        profile_data = {}
        if args.epic:
            profile_data["epic"] = args.epic
        if args.project:
            profile_data["project"] = args.project
        if args.component:
            profile_data["component"] = args.component
        if args.priority:
            profile_data["priority"] = args.priority
        if args.story_points_field:
            profile_data["story_points_field"] = args.story_points_field
        if args.epic_field:
            profile_data["epic_field"] = args.epic_field

        if not profile_data:
            raise ConfigError("No profile settings provided. Use --epic, --project, --component, etc.")

        # Save profile
        profiles[args.profile_name] = profile_data
        self._save_profiles(profiles)

        print(f"✅ Profile '{args.profile_name}' saved successfully")
        print(f"   Configuration file: {config_file}")
        return True

    def _get_profile(self, args: Namespace) -> bool:
        """
        Display a configuration profile.

        Arguments:
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        profiles = self._load_profiles()

        if args.profile_name not in profiles:
            raise ConfigError(f"Profile '{args.profile_name}' not found")

        profile_data = profiles[args.profile_name]

        if args.output == "json":
            print(json.dumps(profile_data, indent=2))
        else:
            print(f"\n📋 Profile: {args.profile_name}")
            print("-" * 40)
            for key, value in profile_data.items():
                print(f"  {key}: {value}")

        return True

    def _list_profiles(self) -> bool:
        """
        List all configuration profiles.

        Returns:
            bool: True if successful
        """
        profiles = self._load_profiles()

        if not profiles:
            print("No configuration profiles found.")
            print("Create one with: rh-issue config set-profile <name> --epic EPIC-123")
            return True

        print("\n📋 Configuration Profiles:")
        print("-" * 40)
        for name in sorted(profiles.keys()):
            print(f"  • {name}")
            for key, value in profiles[name].items():
                print(f"      {key}: {value}")

        return True

    def _delete_profile(self, args: Namespace) -> bool:
        """
        Delete a configuration profile.

        Arguments:
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        profiles = self._load_profiles()

        if args.profile_name not in profiles:
            raise ConfigError(f"Profile '{args.profile_name}' not found")

        del profiles[args.profile_name]
        self._save_profiles(profiles)

        print(f"✅ Profile '{args.profile_name}' deleted successfully")
        return True

    def _get_config_file(self) -> Path:
        """
        Get the path to the configuration file.

        Returns:
            Path: Path to the config file
        """
        # Check for custom config location from environment
        config_dir = EnvFetcher.get("JIRA_CONFIG_DIR", default="")
        if config_dir:
            config_path = Path(config_dir)
        else:
            # Default to ~/.jira-creator/
            config_path = Path.home() / ".jira-creator"

        config_path.mkdir(parents=True, exist_ok=True)
        return config_path / "profiles.json"

    def _load_profiles(self) -> Dict[str, Any]:
        """
        Load all profiles from the configuration file.

        Returns:
            Dict: Dictionary of profiles
        """
        config_file = self._get_config_file()

        if not config_file.exists():
            return {}

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            raise ConfigError(f"Failed to load configuration: {e}") from e

    def _save_profiles(self, profiles: Dict[str, Any]) -> None:
        """
        Save all profiles to the configuration file.

        Arguments:
            profiles: Dictionary of profiles to save

        Raises:
            ConfigError: If save fails
        """
        config_file = self._get_config_file()

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=2)
        except (OSError, IOError) as e:
            raise ConfigError(f"Failed to save configuration: {e}") from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        This plugin doesn't use REST operations.

        Arguments:
            client: JiraClient instance
            **kwargs: Additional arguments

        Returns:
            Empty dict
        """
        return {}


def get_profile_setting(profile_name: str, setting_key: str, default: Any = None) -> Any:
    """
    Utility function to get a setting from a profile.

    Arguments:
        profile_name: Name of the profile
        setting_key: Key of the setting to retrieve
        default: Default value if not found

    Returns:
        The setting value or default
    """
    plugin = ConfigPlugin()
    profiles = plugin._load_profiles()  # pylint: disable=protected-access

    if profile_name not in profiles:
        return default

    return profiles[profile_name].get(setting_key, default)
