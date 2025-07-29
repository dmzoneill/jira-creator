#!/usr/bin/env python
"""
Unassign issue plugin for jira-creator.

This plugin implements the unassign command, allowing users to remove
the assignee from Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import UnassignIssueError
from jira_creator.plugins.base import JiraPlugin


class UnassignPlugin(JiraPlugin):
    """Plugin for unassigning Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "unassign"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Remove the assignee from a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the unassign command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key)
            print(f"✅ Issue {args.issue_key} unassigned")
            return True

        except UnassignIssueError as e:
            msg = f"❌ Failed to unassign issue: {e}"
            print(msg)
            raise UnassignIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to unassign an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"assignee": None}}

        return client.request("PUT", path, json_data=payload)
