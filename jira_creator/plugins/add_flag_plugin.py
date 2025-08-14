#!/usr/bin/env python
"""
Add flag plugin for jira-creator.

This plugin implements the add-flag command, allowing users to flag
Jira issues for attention.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.plugins.base import JiraPlugin


class AddFlagPlugin(JiraPlugin):
    """Plugin for adding flags to Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "add-flag"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Add a flag to a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the add-flag command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key)
            print(f"🚩 Flag added to {args.issue_key}")
            return True

        except Exception as e:
            msg = f"❌ Failed to add flag: {e}"
            print(msg)
            raise ValueError(msg) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to add a flag.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]

        path = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
        payload = {"issueKeys": [issue_key], "flag": True}

        return client.request("POST", path, json_data=payload)
