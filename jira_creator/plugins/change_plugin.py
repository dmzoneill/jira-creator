#!/usr/bin/env python
"""
Change (alias for change-type) plugin for jira-creator.

This plugin provides the 'change' command as an alias to 'change-type'
for backward compatibility with the original CLI.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import ChangeTypeError
from jira_creator.plugins.base import JiraPlugin


class ChangePlugin(JiraPlugin):
    """Plugin for changing issue types (alias for change-type)."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "change"

    @property
    def help_text(self) -> str:
        """Return the command help text."""
        return "Change issue type"

    # jscpd:ignore-start
    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments with the argument parser."""
        parser.add_argument("issue_key", help="The Jira issue id/key")
        parser.add_argument("new_type", help="New issue type")

    def execute(self, client: Any, args: Namespace) -> bool:
        """Execute the change type command."""
        # jscpd:ignore-end
        try:
            self.rest_operation(client, issue_key=args.issue_key, new_type=args.new_type)
            print(f"✅ Changed type of {args.issue_key} to {args.new_type}")
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
            **kwargs: Must contain 'issue_key' and 'new_type'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        new_type = kwargs["new_type"]

        # Implement change_issue_type logic directly
        # This is a simple implementation - may need more complex logic for some Jira instances
        payload = {"fields": {"issuetype": {"name": new_type}}}
        client.request("PUT", f"/rest/api/2/issue/{issue_key}", json_data=payload)
        return {"success": True}
