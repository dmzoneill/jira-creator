#!/usr/bin/env python
"""
Change type plugin for jira-creator.

This plugin implements the change-type command, allowing users to change
the issue type of Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import ChangeTypeError
from jira_creator.plugins.base import JiraPlugin


class ChangeTypePlugin(JiraPlugin):
    """Plugin for changing issue types."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "change-type"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Change the type of a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument(
            "new_type",
            choices=["bug", "story", "epic", "task", "spike"],
            help="The new issue type",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the change-type command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key, new_type=args.new_type)
            print(f"✅ Issue type changed to '{args.new_type}'")
            return True

        except ChangeTypeError as e:
            msg = f"❌ Failed to change issue type: {e}"
            print(msg)
            raise ChangeTypeError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to change issue type.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'new_type'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        new_type = kwargs["new_type"]

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"issuetype": {"name": new_type.capitalize()}}}

        return client.request("PUT", path, json_data=payload)
