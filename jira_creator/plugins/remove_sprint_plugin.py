#!/usr/bin/env python
"""
Remove from sprint plugin for jira-creator.

This plugin implements the remove-sprint command, allowing users to remove
issues from their current sprint and move them to the backlog.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import RemoveFromSprintError
from jira_creator.plugins.base import JiraPlugin


class RemoveSprintPlugin(JiraPlugin):
    """Plugin for removing issues from sprints."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "remove-sprint"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Remove an issue from its current sprint"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the remove-sprint command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key)
            print("✅ Removed from sprint")
            return True

        except RemoveFromSprintError as e:
            msg = f"❌ Failed to remove from sprint: {e}"
            print(msg)
            raise RemoveFromSprintError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to remove issue from sprint.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]

        # Move issue to backlog
        path = "/rest/agile/1.0/backlog/issue"
        payload = {"issues": [issue_key]}

        response = client.request("POST", path, json_data=payload)
        print(f"✅ Moved {issue_key} to backlog")

        return response
