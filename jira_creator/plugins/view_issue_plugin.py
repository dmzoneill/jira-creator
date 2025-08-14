#!/usr/bin/env python
"""
View issue plugin for jira-creator.

This plugin implements the view-issue command, allowing users to view
detailed information about a Jira issue.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import ViewIssueError
from jira_creator.plugins.base import JiraPlugin


class ViewIssuePlugin(JiraPlugin):
    """Plugin for viewing Jira issue details."""

    # Allowed fields for display
    ALLOWED_KEYS = [
        "acceptance criteria",
        "blocked",
        "blocked reason",
        "assignee",
        "component/s",
        "created",
        "creator",
        "description",
        "issue type",
        "labels",
        "priority",
        "project",
        "reporter",
        "sprint",
        "status",
        "story points",
        "summary",
        "updated",
        "workstream",
    ]

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "view-issue"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "View detailed information about a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the view-issue command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            issue_data = self.rest_operation(client, issue_key=args.issue_key)

            # Process and display the issue
            self._display_issue(issue_data, args.issue_key)

            return True

        except ViewIssueError as e:
            msg = f"❌ Failed to view issue: {e}"
            print(msg)
            raise ViewIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to get issue details.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: Issue data
        """
        issue_key = kwargs["issue_key"]

        path = f"/rest/api/2/issue/{issue_key}"
        return client.request("GET", path)

    def _display_issue(self, issue_data: Dict[str, Any], issue_key: str) -> None:
        """Display issue data in a formatted way."""
        fields = issue_data.get("fields", {})

        # Get custom field mappings
        custom_fields = self._get_custom_field_mappings()

        # Process fields
        processed_fields = self._process_fields(fields, custom_fields)

        # Display header
        print(f"\n📋 Issue: {issue_key}")
        print("=" * 50)

        # Display fields
        max_key_length = max(len(key) for key in processed_fields)

        for key in self.ALLOWED_KEYS:
            if key in processed_fields:
                value = processed_fields[key]
                formatted_value = self._format_value(value)
                print(f"{key.ljust(max_key_length)} : {formatted_value}")

        print("=" * 50)

    def _get_custom_field_mappings(self) -> Dict[str, str]:
        """Get custom field mappings from environment."""
        return {
            EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD", ""): "acceptance criteria",
            EnvFetcher.get("JIRA_BLOCKED_FIELD", ""): "blocked",
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD", ""): "blocked reason",
            EnvFetcher.get("JIRA_STORY_POINTS_FIELD", ""): "story points",
            EnvFetcher.get("JIRA_SPRINT_FIELD", ""): "sprint",
            EnvFetcher.get("JIRA_WORKSTREAM_FIELD", ""): "workstream",
        }

    def _process_fields(self, fields: Dict[str, Any], custom_fields: Dict[str, str]) -> Dict[str, Any]:
        """Process and normalize field names."""
        processed = {}

        for field_key, field_value in fields.items():
            # Map custom fields
            if field_key in custom_fields:
                field_name = custom_fields[field_key]
            else:
                # Normalize standard field names
                field_name = field_key.replace("_", " ").lower()

            # Handle special fields
            if field_name == "components":
                field_name = "component/s"
                field_value = [c["name"] for c in field_value] if field_value else []
            elif field_name == "issuetype":
                field_name = "issue type"
                field_value = field_value.get("name") if field_value else None
            elif field_name in ["assignee", "reporter", "creator"]:
                field_value = field_value.get("displayName") if field_value else "Unassigned"
            elif field_name == "priority":
                field_value = field_value.get("name") if field_value else None
            elif field_name == "status":
                field_value = field_value.get("name") if field_value else None
            elif field_name == "project":
                field_value = field_value.get("key") if field_value else None

            if field_value is not None:
                processed[field_name] = field_value

        return processed

    def _format_value(self, value: Any) -> str:
        """Format a field value for display."""
        if isinstance(value, dict):
            return str(value)
        if isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else "None"
        if isinstance(value, str) and "\n" in value:
            # Handle multiline strings
            lines = value.split("\n")
            if len(lines) > 3:
                return lines[0] + "... (truncated)"
            return " / ".join(lines)
        return str(value) if value else "None"
