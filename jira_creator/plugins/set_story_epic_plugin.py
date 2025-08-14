#!/usr/bin/env python
"""
Set story epic plugin for jira-creator.

This plugin implements the set-story-epic command, allowing users to link
a story to an epic in Jira.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import SetStoryEpicError
from jira_creator.plugins.base import JiraPlugin


class SetStoryEpicPlugin(JiraPlugin):
    """Plugin for setting the epic of a story."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "set-story-epic"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Link a story to an epic"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The story issue key (e.g., PROJ-123)")
        parser.add_argument("epic_key", help="The epic issue key (e.g., PROJ-100)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the set-story-epic command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key, epic_key=args.epic_key)
            print(f"✅ Story {args.issue_key} linked to epic {args.epic_key}")
            return True

        except SetStoryEpicError as e:
            msg = f"❌ Failed to set epic: {e}"
            print(msg)
            raise SetStoryEpicError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set story epic.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'epic_key'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        epic_key = kwargs["epic_key"]

        # Get epic field from environment
        epic_field = EnvFetcher.get("JIRA_EPIC_FIELD")
        if not epic_field:
            raise SetStoryEpicError("JIRA_EPIC_FIELD not set in environment")

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {epic_field: epic_key}}

        return client.request("PUT", path, json_data=payload)
