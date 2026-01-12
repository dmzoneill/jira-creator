#!/usr/bin/env python
"""
View issue plugin for jira-creator.

This plugin implements the view-issue command, allowing users to view
detailed information about a Jira issue.
"""

import re
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin


class ViewIssueError(Exception):
    """Exception raised when viewing an issue fails."""


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
        "epic",
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

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Search & View"

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "ViewIssueError": ViewIssueError,
        }

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["view-issue AAP-12345", "view-issue AAP-12345 --output json"]

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
            Dict[str, Any]: Issue data including comments
        """
        issue_key = kwargs["issue_key"]

        path = f"/rest/api/2/issue/{issue_key}"
        params = {"expand": "renderedFields"}
        issue_data = client.request("GET", path, params=params)

        comments_path = f"/rest/api/2/issue/{issue_key}/comment"
        comments_response = client.request("GET", comments_path)
        if comments_response:
            issue_data["_comments"] = comments_response.get("comments", [])

        return issue_data

    def _display_issue(self, issue_data: Dict[str, Any], issue_key: str) -> None:
        """Display issue data in a formatted way."""
        fields = issue_data.get("fields", {})
        rendered_fields = issue_data.get("renderedFields", {})
        comments = issue_data.get("_comments", [])

        custom_fields = self._get_custom_field_mappings()
        processed_fields = self._process_fields(fields, custom_fields)

        self._print_header(issue_key)
        self._print_fields(processed_fields)
        self._print_description(fields, rendered_fields)
        self._print_comments(comments)

    def _print_header(self, issue_key: str) -> None:
        """Print the issue header."""
        print(f"\n📋 Issue: {issue_key}")
        print("=" * 70)

    def _print_fields(self, processed_fields: Dict[str, Any]) -> None:
        """Print the issue fields."""
        display_keys = [k for k in self.ALLOWED_KEYS if k != "description"]
        max_key_length = max(len(key) for key in display_keys) if display_keys else 20

        for key in display_keys:
            if key in processed_fields:
                formatted_value = self._format_value(processed_fields[key])
                print(f"{key.ljust(max_key_length)} : {formatted_value}")

    def _print_description(self, fields: Dict[str, Any], rendered_fields: Dict[str, Any]) -> None:
        """Print the issue description."""
        print("\n" + "=" * 70)
        print("📝 DESCRIPTION")
        print("-" * 70)

        rendered_desc = rendered_fields.get("description")
        if rendered_desc:
            clean_desc = self._strip_html(rendered_desc)
            print(clean_desc.strip())
        else:
            print(fields.get("description") or "No description provided.")

    def _strip_html(self, html_text: str) -> str:
        """Strip HTML tags and decode entities."""
        clean = re.sub(r"<[^>]+>", "", html_text)
        clean = clean.replace("&nbsp;", " ").replace("&amp;", "&")
        return clean.replace("&lt;", "<").replace("&gt;", ">")

    def _print_comments(self, comments: List[Dict[str, Any]]) -> None:
        """Print the issue comments."""
        print("\n" + "=" * 70)
        print(f"💬 COMMENTS ({len(comments)})")
        print("-" * 70)

        if not comments:
            print("No comments yet.")
            print("\n" + "=" * 70)
            return

        for i, comment in enumerate(comments, 1):
            self._print_single_comment(i, comment)

        print("\n" + "=" * 70)

    def _print_single_comment(self, index: int, comment: Dict[str, Any]) -> None:
        """Print a single comment."""
        author = (comment.get("author") or {}).get("displayName", "Unknown")
        created = comment.get("created", "")[:10]
        body = comment.get("body", "")

        print(f"\n[{index}] {author} - {created}")
        print("-" * 40)
        print(body[:500] + "... (truncated)" if len(body) > 500 else body)

    def _get_custom_field_mappings(self) -> Dict[str, str]:
        """Get custom field mappings from environment."""
        return {
            EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD", ""): "acceptance criteria",
            EnvFetcher.get("JIRA_BLOCKED_FIELD", ""): "blocked",
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD", ""): "blocked reason",
            EnvFetcher.get("JIRA_EPIC_FIELD", ""): "epic",
            EnvFetcher.get("JIRA_STORY_POINTS_FIELD", ""): "story points",
            EnvFetcher.get("JIRA_SPRINT_FIELD", ""): "sprint",
            EnvFetcher.get("JIRA_WORKSTREAM_FIELD", ""): "workstream",
        }

    def _process_fields(self, fields: Dict[str, Any], custom_fields: Dict[str, str]) -> Dict[str, Any]:
        """Process and normalize field names."""
        processed = {}

        for field_key, field_value in fields.items():
            field_name = custom_fields.get(field_key, field_key.replace("_", " ").lower())
            field_name, field_value = self._transform_field(field_name, field_value)

            if field_value is not None:
                processed[field_name] = field_value

        return processed

    def _transform_field(self, field_name: str, field_value: Any) -> tuple:
        """Transform a single field based on its name."""
        # Define field transformations
        transformers = {
            "components": lambda v: ("component/s", [c["name"] for c in v] if v else []),
            "issuetype": lambda v: ("issue type", v.get("name") if v else None),
            "project": lambda v: (field_name, v.get("key") if v else None),
            "sprint": lambda v: (field_name, self._extract_sprint_names(v)),
        }

        # Check for exact match first
        if field_name in transformers:
            return transformers[field_name](field_value)

        # Handle grouped field types
        if field_name in ["assignee", "reporter", "creator"]:
            return field_name, field_value.get("displayName") if field_value else "Unassigned"

        if field_name in ["priority", "status"]:
            return field_name, field_value.get("name") if field_value else None

        if field_name in ["blocked", "workstream"]:
            return field_name, self._extract_option_value(field_value)

        if field_name == "epic":
            return field_name, self._extract_epic_key(field_value)

        return field_name, field_value

    def _extract_epic_key(self, field_value: Any) -> Optional[str]:
        """Extract epic key from epic field value."""
        if field_value is None:
            return None
        if isinstance(field_value, str):
            return field_value
        if isinstance(field_value, dict):
            return field_value.get("key") or field_value.get("name")
        return str(field_value)

    def _extract_option_value(self, field_value: Any) -> Optional[str]:
        """Extract value from custom field option objects."""
        if isinstance(field_value, list) and field_value:
            values = [item.get("value", str(item)) for item in field_value if isinstance(item, dict)]
            return ", ".join(values) if values else str(field_value)
        if isinstance(field_value, dict):
            return field_value.get("value", str(field_value))
        return field_value

    def _extract_sprint_names(self, field_value: Any) -> Optional[str]:
        """Extract sprint names from sprint field value."""
        if isinstance(field_value, list):
            sprint_names = []
            for sprint_str in field_value:
                name = self._parse_sprint_name(sprint_str)
                if name:
                    sprint_names.append(name)
            return ", ".join(sprint_names) if sprint_names else None

        if isinstance(field_value, str):
            return self._parse_sprint_name(field_value) or field_value

        return None

    def _parse_sprint_name(self, sprint_str: str) -> Optional[str]:
        """Parse sprint name from sprint string representation."""
        if isinstance(sprint_str, str):
            match = re.search(r"name=([^,\]]+)", sprint_str)
            return match.group(1) if match else None
        return None

    def _format_value(self, value: Any) -> str:
        """Format a field value for display."""
        if isinstance(value, dict):
            return str(value)
        if isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else "None"
        if isinstance(value, str) and "\n" in value:
            lines = value.split("\n")
            return lines[0] + "... (truncated)" if len(lines) > 3 else " / ".join(lines)
        return str(value) if value else "None"
