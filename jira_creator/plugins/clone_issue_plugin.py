#!/usr/bin/env python
"""
Clone issue plugin for jira-creator.

This plugin implements the clone-issue command, allowing users to create
a copy of an existing Jira issue.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import CloneIssueError
from jira_creator.plugins.base import JiraPlugin


class CloneIssuePlugin(JiraPlugin):
    """Plugin for cloning Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "clone-issue"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Create a copy of an existing Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key to clone (e.g., PROJ-123)")
        parser.add_argument(
            "-s",
            "--summary-suffix",
            default=" (Clone)",
            help="Suffix to add to the cloned issue summary (default: ' (Clone)')",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the clone-issue command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # First, get the original issue details
            original_issue = self._get_issue_details(client, args.issue_key)

            # Clone the issue
            cloned_issue = self.rest_operation(
                client,
                original_issue=original_issue,
                summary_suffix=args.summary_suffix,
            )

            cloned_key = cloned_issue.get("key")
            print(f"✅ Issue cloned: {args.issue_key} → {cloned_key}")

            return True

        except CloneIssueError as e:
            msg = f"❌ Failed to clone issue: {e}"
            print(msg)
            raise CloneIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to clone an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'original_issue' and 'summary_suffix'

        Returns:
            Dict[str, Any]: Created issue data
        """
        original = kwargs["original_issue"]
        suffix = kwargs["summary_suffix"]

        # Extract fields from original issue
        fields = original.get("fields", {})

        # Build payload for new issue
        payload = {
            "fields": {
                "project": {"key": fields.get("project", {}).get("key")},
                "summary": fields.get("summary", "") + suffix,
                "description": fields.get("description", ""),
                "issuetype": {"name": fields.get("issuetype", {}).get("name")},
                "priority": {"name": fields.get("priority", {}).get("name", "Normal")},
            }
        }

        # Copy additional fields if present
        if fields.get("components"):
            payload["fields"]["components"] = fields["components"]

        if fields.get("labels"):
            payload["fields"]["labels"] = fields["labels"]

        if fields.get("versions"):
            payload["fields"]["versions"] = fields["versions"]

        # Create the cloned issue
        path = "/rest/api/2/issue/"
        return client.request("POST", path, json_data=payload)

    def _get_issue_details(self, client: Any, issue_key: str) -> Dict[str, Any]:
        """Get the details of an issue to clone."""
        path = f"/rest/api/2/issue/{issue_key}"
        return client.request("GET", path)
