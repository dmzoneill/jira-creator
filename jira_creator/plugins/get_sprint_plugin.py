#!/usr/bin/env python
"""
Get sprint plugin for jira-creator.

This plugin implements the get-sprint command, allowing users to get
information about the current active sprint.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.base import JiraPlugin


class GetSprintPlugin(JiraPlugin):
    """Plugin for getting current sprint information."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "get-sprint"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Get the current active sprint"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument(
            "-b",
            "--board-id",
            help="Board ID (uses JIRA_BOARD_ID env var if not specified)",
            default=None,
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the get-sprint command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Get board ID
            board_id = args.board_id or EnvFetcher.get("JIRA_BOARD_ID")

            if not board_id:
                print("❌ No board ID specified. Use --board-id or set JIRA_BOARD_ID")
                return False

            # Get active sprint
            sprint_data = self.rest_operation(client, board_id=board_id)

            if sprint_data and sprint_data.get("values"):
                sprint = sprint_data["values"][0]
                print(f"🏃 Active Sprint: {sprint['name']}")
                print(f"   State: {sprint.get('state', 'Unknown')}")
                print(f"   ID: {sprint.get('id')}")

                if sprint.get("startDate"):
                    print(f"   Start: {sprint['startDate'][:10]}")
                if sprint.get("endDate"):
                    print(f"   End: {sprint['endDate'][:10]}")
            else:
                print("📭 No active sprint found")

            return True

        except Exception as e:
            msg = f"❌ Failed to get sprint: {e}"
            print(msg)
            raise ValueError(msg) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to get active sprint.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'board_id'

        Returns:
            Dict[str, Any]: Sprint data
        """
        board_id = kwargs["board_id"]

        # Get active sprints
        path = f"/rest/agile/1.0/board/{board_id}/sprint?state=active"
        return client.request("GET", path)
