#!/usr/bin/env python
"""
Set priority plugin for jira-creator.

This plugin implements the set-priority command, allowing users to
change the priority of Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import SetPriorityError
from jira_creator.plugins.base import JiraPlugin


class SetPriorityPlugin(JiraPlugin):
    """Plugin for setting the priority of Jira issues."""

    # Priority mapping
    PRIORITIES = {
        "critical": "Critical",
        "major": "Major",
        "normal": "Normal",
        "minor": "Minor",
    }

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "set-priority"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Set the priority of a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument(
            "priority",
            choices=["critical", "major", "normal", "minor"],
            help="Priority level to set",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the set-priority command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful

        Raises:
            SetPriorityError: If setting priority fails
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key, priority=args.priority)
            print(f"✅ Priority set to '{args.priority}'")
            return True
        except SetPriorityError as e:
            msg = f"❌ Failed to set priority: {e}"
            print(msg)
            raise SetPriorityError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set priority.

        Arguments:
            client: JiraClient instance
            **kwargs: Must contain 'issue_key' and 'priority'

        Returns:
            Dict[str, Any]: API response (empty dict for PUT requests)
        """
        issue_key = kwargs["issue_key"]
        priority = kwargs["priority"]

        # Normalize priority
        priority_name = self.PRIORITIES.get(priority.lower(), "Normal")  # Default if not found

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"priority": {"name": priority_name}}}

        return client.request("PUT", path, json_data=payload)
