#!/usr/bin/env python
"""
Remove flag plugin for jira-creator.

This plugin implements the remove-flag command, allowing users to remove
flags from Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import RemoveFlagError
from jira_creator.plugins.base import JiraPlugin


class RemoveFlagPlugin(JiraPlugin):
    """Plugin for removing flags from Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "remove-flag"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Remove a flag from a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the remove-flag command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key)
            print(f"✅ Removed flag from issue '{args.issue_key}'")
            return True

        except RemoveFlagError as e:
            msg = f"❌ Failed to remove flag: {e}"
            print(msg)
            raise RemoveFlagError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to remove a flag.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]

        path = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
        payload = {"issueKeys": [issue_key], "flag": False}

        return client.request("POST", path, json_data=payload)
