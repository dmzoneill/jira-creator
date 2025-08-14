#!/usr/bin/env python
"""
Add to sprint plugin for jira-creator.

This plugin implements the add-to-sprint command, allowing users to add
issues to sprints and optionally assign them.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import AddSprintError
from jira_creator.plugins.base import JiraPlugin


class AddToSprintPlugin(JiraPlugin):
    """Plugin for adding issues to sprints."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "add-to-sprint"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Add an issue to a sprint and optionally assign it"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("sprint_name", help="The name of the sprint")
        parser.add_argument(
            "-a",
            "--assignee",
            help="Assignee username (defaults to current user if not specified)",
            default=None,
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the add-to-sprint command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(
                client,
                issue_key=args.issue_key,
                sprint_name=args.sprint_name,
                assignee=args.assignee,
            )
            print(f"✅ Added to sprint '{args.sprint_name}'")
            return True

        except AddSprintError as e:
            msg = f"❌ {e}"
            print(msg)
            raise AddSprintError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operations to add issue to sprint.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key', 'sprint_name', and 'assignee'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        sprint_name = kwargs["sprint_name"]
        assignee = kwargs.get("assignee")

        # Get board ID from environment
        board_id = EnvFetcher.get("JIRA_BOARD_ID")
        if not board_id:
            raise AddSprintError("❌ JIRA_BOARD_ID not set in environment")

        # Find sprint ID by name
        sprint_id = self._find_sprint_id(client, board_id, sprint_name)

        if not sprint_id:
            raise AddSprintError(f"❌ Could not find sprint named '{sprint_name}'")

        # Handle assignment
        if assignee is None or assignee == "":
            # Get current user
            user = client.request("GET", "/rest/api/2/myself")
            assignee = user.get("name")

        # Assign the issue
        client.request(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json_data={"fields": {"assignee": {"name": assignee}}},
        )

        # Add to sprint
        response = client.request(
            "POST",
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            json_data={"issues": [issue_key]},
        )

        print(f"✅ Added {issue_key} to sprint '{sprint_name}' on board {board_id}")

        return response

    def _find_sprint_id(self, client: Any, board_id: str, sprint_name: str) -> Optional[int]:
        """
        Find sprint ID by name.

        Arguments:
            client: JiraClient instance
            board_id: Board ID
            sprint_name: Sprint name to search for

        Returns:
            Sprint ID or None if not found
        """
        start_at = 0
        max_results = 50

        while True:
            path = f"/rest/agile/1.0/board/{board_id}/sprint" f"?startAt={start_at}&maxResults={max_results}"
            res = client.request("GET", path)
            sprints: List[Dict[str, Any]] = res.get("values", [])

            for sprint in sprints:
                if sprint["name"] == sprint_name:
                    return sprint["id"]

            if res.get("isLast", False) or len(sprints) < max_results:
                break

            start_at += max_results

        return None
