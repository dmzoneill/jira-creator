#!/usr/bin/env python
"""
Assign issue plugin for jira-creator.

This plugin implements the assign command, allowing users to assign
Jira issues to specific users.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import AssignIssueError
from jira_creator.plugins.base import JiraPlugin


class AssignPlugin(JiraPlugin):
    """Plugin for assigning Jira issues to users."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "assign"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Assign a Jira issue to a user"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("assignee", help="Username of the person to assign the issue to")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the assign command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key, assignee=args.assignee)
            print(f"✅ Issue {args.issue_key} assigned to {args.assignee}")
            return True

        except AssignIssueError as e:
            msg = f"❌ Failed to assign issue: {e}"
            print(msg)
            raise AssignIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to assign an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'assignee'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        assignee = kwargs["assignee"]

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"assignee": {"name": assignee}}}

        return client.request("PUT", path, json_data=payload)
