#!/usr/bin/env python
"""
Unblock issue plugin for jira-creator.

This plugin implements the unblock command, allowing users to remove
the blocked status from Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import UnBlockError
from jira_creator.plugins.base import JiraPlugin


class UnblockPlugin(JiraPlugin):
    """Plugin for unblocking Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "unblock"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Remove the blocked status from a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the unblock command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key)
            print(f"✅ {args.issue_key} marked as unblocked")
            return True

        except UnBlockError as e:
            msg = f"❌ Failed to unblock {args.issue_key}: {e}"
            print(msg)
            raise UnBlockError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to unblock an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]

        # Get field IDs from environment
        blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD")
        reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {blocked_field: {"value": False}, reason_field: ""}}

        return client.request("PUT", path, json_data=payload)
