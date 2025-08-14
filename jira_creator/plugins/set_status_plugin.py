#!/usr/bin/env python
"""
Set status plugin for jira-creator.

This plugin implements the set-status command, allowing users to
change the status of Jira issues with support for transitions.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional

from jira_creator.exceptions.exceptions import SetStatusError
from jira_creator.plugins.base import JiraPlugin


class SetStatusPlugin(JiraPlugin):
    """Plugin for setting the status of Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "set-status"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Set the status of a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("status", help="The status to transition to")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the set-status command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key, status=args.status)
            print(f"✅ Status set to '{args.status}'")

            # Handle special refinement status actions
            if args.status.lower() == "refinement":
                self._handle_refinement_status(client, args.issue_key)

            return True

        except SetStatusError as e:
            msg = f"❌ Failed to set status: {e}"
            print(msg)
            raise SetStatusError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set status.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'status'

        Returns:
            Dict[str, Any]: Empty dict (transition endpoint returns no content)
        """
        issue_key = kwargs["issue_key"]
        status = kwargs["status"]

        # Get available transitions
        transitions = self._get_transitions(client, issue_key)

        # Find matching transition
        transition_id = self._find_transition_id(transitions, status)

        if not transition_id:
            available = [t["name"] for t in transitions]
            raise SetStatusError(f"Status '{status}' not available. Available transitions: {', '.join(available)}")

        # Perform transition
        path = f"/rest/api/2/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}

        return client.request("POST", path, json_data=payload)

    def _get_transitions(self, client: Any, issue_key: str) -> List[Dict[str, Any]]:
        """Get available transitions for an issue."""
        path = f"/rest/api/2/issue/{issue_key}/transitions"
        response = client.request("GET", path)
        return response.get("transitions", [])

    def _find_transition_id(self, transitions: List[Dict], status: str) -> Optional[str]:
        """Find transition ID for the given status name."""
        status_lower = status.lower()

        for transition in transitions:
            if transition["name"].lower() == status_lower:
                return transition["id"]

        return None

    def _handle_refinement_status(self, client: Any, issue_key: str) -> None:
        """Handle special actions for refinement status."""
        try:
            # Move to top of backlog
            print("📌 Moving issue to top of backlog...")
            client.request(
                "PUT",
                "/rest/greenhopper/1.0/sprint/rank",
                json_data={"issueToMove": issue_key, "moveToTop": True},
            )

            # Get issue details to find epic
            issue_details = client.request("GET", f"/rest/api/2/issue/{issue_key}")
            epic_key = issue_details.get("fields", {}).get("parent", {}).get("key")

            if epic_key:
                # Move to top of epic
                print(f"📌 Moving issue to top of epic {epic_key}...")
                client.request(
                    "PUT",
                    "/rest/greenhopper/1.0/rank/global/first",
                    json_data={"issueToMove": issue_key, "parentKey": epic_key},
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Don't fail the whole operation if ranking fails
            print(f"⚠️  Could not complete ranking operations: {e}")
