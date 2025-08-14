#!/usr/bin/env python
"""
List sprints plugin for jira-creator.

This plugin implements the list-sprints command, allowing users to list
all sprints for a given board.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.base import JiraPlugin


class ListSprintsPlugin(JiraPlugin):
    """Plugin for listing sprints on a board."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "list-sprints"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "List all sprints for a board"

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
        Execute the list-sprints command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Get board ID from args or environment
            board_id = args.board_id or EnvFetcher.get("JIRA_BOARD_ID")

            if not board_id:
                print("❌ No board ID specified. Use --board-id or set JIRA_BOARD_ID")
                return False

            sprints = self.rest_operation(client, board_id=board_id)

            # Display sprints
            print(f"📋 Sprints for board {board_id}:")
            for sprint in sprints:
                status = sprint.get("state", "unknown")
                print(f"    - {sprint['name']} ({status})")

            print(f"\nTotal: {len(sprints)} sprints")
            return True

        except Exception as e:
            msg = f"❌ Failed to list sprints: {e}"
            print(msg)
            raise ValueError(msg) from e

    def rest_operation(self, client: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform the REST API operation to list sprints.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'board_id'

        Returns:
            List[Dict[str, Any]]: List of sprint data
        """
        board_id = kwargs["board_id"]
        all_sprints = []
        start_at = 0
        max_results = 50

        while True:
            path = f"/rest/agile/1.0/board/{board_id}/sprint" f"?startAt={start_at}&maxResults={max_results}"

            res = client.request("GET", path)
            sprints = res.get("values", [])
            all_sprints.extend(sprints)

            if res.get("isLast", False) or len(sprints) < max_results:
                break

            start_at += max_results

        return all_sprints
