#!/usr/bin/env python
"""
Block issue plugin for jira-creator.

This plugin implements the block command, allowing users to mark
Jira issues as blocked with a reason.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import BlockError
from jira_creator.plugins.base import JiraPlugin


class BlockPlugin(JiraPlugin):
    """Plugin for marking Jira issues as blocked."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "block"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Mark a Jira issue as blocked"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("reason", nargs="+", help="The reason for blocking the issue")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the block command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        # Join reason words into a single string
        reason = " ".join(args.reason)

        try:
            self.rest_operation(client, issue_key=args.issue_key, reason=reason)
            print(f"✅ {args.issue_key} marked as blocked: {reason}")
            return True

        except BlockError as e:
            msg = f"❌ Failed to mark {args.issue_key} as blocked: {e}"
            print(msg)
            raise BlockError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to block an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'reason'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        reason = kwargs["reason"]

        # Get field IDs from environment
        blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD")
        reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {
            "fields": {
                blocked_field: {"id": "14656"},  # "True" option ID
                reason_field: reason,
            }
        }

        return client.request("PUT", path, json_data=payload)
