#!/usr/bin/env python
"""
List fields plugin for jira-creator.

This plugin implements the list-fields command, allowing users to discover
custom field IDs on their Jira instance. Useful when migrating between
Jira Data Center and Cloud where custom field IDs change.
"""

from argparse import ArgumentParser, Namespace
from typing import Any

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import MissingConfigVariable


class ListFieldsError(Exception):
    """Exception raised when listing fields fails."""


# Map of env var names to their descriptions
FIELD_ENV_VARS = {
    "JIRA_EPIC_FIELD": "Epic Link",
    "JIRA_EPIC_NAME_FIELD": "Epic Name",
    "JIRA_ACCEPTANCE_CRITERIA_FIELD": "Acceptance Criteria",
    "JIRA_BLOCKED_FIELD": "Blocked",
    "JIRA_BLOCKED_REASON_FIELD": "Blocked Reason",
    "JIRA_STORY_POINTS_FIELD": "Story Points",
    "JIRA_SPRINT_FIELD": "Sprint",
    "JIRA_WORKSTREAM_FIELD": "Workstream",
}


class ListFieldsPlugin(JiraPlugin):
    """Plugin for listing Jira custom fields."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "list-fields"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "List custom fields from the Jira instance"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Search & View"

    @property
    def example_commands(self) -> list[str]:
        """Return example commands."""
        return [
            "list-fields",
            "list-fields --filter sprint",
            "list-fields --custom-only",
            "list-fields --check-config",
        ]

    def get_plugin_exceptions(self) -> dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "ListFieldsError": ListFieldsError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument(
            "-f",
            "--filter",
            default="",
            help="Filter fields by name (case-insensitive substring match)",
        )
        parser.add_argument(
            "--custom-only",
            action="store_true",
            default=False,
            help="Show only custom fields",
        )
        parser.add_argument(
            "--check-config",
            action="store_true",
            default=False,
            help="Compare configured env vars against available fields",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """Execute the list-fields command."""
        try:
            fields = self.rest_operation(client)

            if args.check_config:
                self._check_config(fields, client)
                return True

            if args.custom_only:
                fields = [f for f in fields if f.get("custom")]

            if args.filter:
                filter_lower = args.filter.lower()
                fields = [
                    f
                    for f in fields
                    if filter_lower in f.get("name", "").lower() or filter_lower in f.get("id", "").lower()
                ]

            if not fields:
                print("No fields found matching your criteria.")
                return True

            self.display_fields(fields)
            return True

        except ListFieldsError as e:
            msg = f"Failed to list fields: {e}"
            print(msg)
            raise ListFieldsError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> list[dict[str, Any]]:
        """Fetch all fields from the Jira instance."""
        return client.request("GET", "/rest/api/2/field")

    def display_fields(self, fields: list[dict[str, Any]]) -> None:
        """Display fields in a table format."""
        # Sort by ID for consistent output
        fields = sorted(fields, key=lambda f: f.get("id", ""))

        print(f"\n{'ID':<35} {'Name':<40} {'Custom':<8}")
        print("=" * 83)

        for field in fields:
            field_id = field.get("id", "")
            name = field.get("name", "")
            custom = "Yes" if field.get("custom") else "No"
            print(f"{field_id:<35} {name:<40} {custom:<8}")

        print(f"\nTotal: {len(fields)} fields")

    def _check_config(self, fields: list[dict[str, Any]], client: Any) -> None:
        """Compare configured env vars against available fields on the instance."""
        # Build lookup from field ID to field name
        field_map: dict[str, str] = {f["id"]: f["name"] for f in fields if f.get("id")}
        # Build reverse lookup from name (lowered) to field IDs
        name_to_ids: dict[str, list[str]] = {}
        for f in fields:
            name = f.get("name", "").lower()
            if name and f.get("id"):
                name_to_ids.setdefault(name, []).append(f["id"])

        instance_type = "Cloud" if getattr(client, "is_cloud", False) else "Data Center/Server"
        print(f"\nField Configuration Check ({instance_type})")
        print("=" * 80)

        for env_var, description in FIELD_ENV_VARS.items():
            configured_id = self._get_configured_value(env_var)
            self.check_single_field(env_var, description, configured_id, field_map, name_to_ids)

    @staticmethod
    def _get_configured_value(env_var: str) -> str | None:
        """Get the configured value of an env var, returning None if not set."""
        try:
            val = EnvFetcher.get(env_var, default="")
            return val if val else None
        except (MissingConfigVariable, KeyError, ValueError):
            return None

    @staticmethod
    def check_single_field(
        env_var: str,
        description: str,
        configured_id: str | None,
        field_map: dict[str, str],
        name_to_ids: dict[str, list[str]],
    ) -> None:
        """Check a single field configuration and print the result."""
        if not configured_id:
            print(f"\n  {env_var} ({description})")
            print("    Status: NOT CONFIGURED")
            # Suggest matching fields by description
            suggestions = name_to_ids.get(description.lower(), [])
            if suggestions:
                print(f"    Suggestion: {', '.join(suggestions)}")
            return

        print(f"\n  {env_var} ({description})")
        print(f"    Configured: {configured_id}")

        if configured_id in field_map:
            actual_name = field_map[configured_id]
            print(f"    Instance:   {actual_name}")
            print("    Status: OK")
        else:
            print("    Status: FIELD NOT FOUND on this instance")
            # Try to find by description name
            suggestions = name_to_ids.get(description.lower(), [])
            if suggestions:
                for sid in suggestions:
                    print(f"    Suggestion: {sid} ({field_map.get(sid, '?')})")
