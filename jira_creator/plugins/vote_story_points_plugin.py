#!/usr/bin/env python
"""
Vote story points plugin for jira-creator.

This plugin implements the vote-story-points command, allowing users to
vote on story points for Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError
from jira_creator.plugins.base import JiraPlugin


class VoteStoryPointsPlugin(JiraPlugin):
    """Plugin for voting on story points."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "vote-story-points"

    @property
    def help_text(self) -> str:
        """Return the command help text."""
        return "Vote on story points"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments with the argument parser."""
        parser.add_argument("issue_key", help="The Jira issue id/key")
        parser.add_argument("points", help="Number of story points to vote")

    def execute(self, client: Any, args: Namespace) -> bool:
        """Execute the vote story points command."""
        try:
            points = int(args.points)
        except ValueError:
            print("❌ Story points must be an integer.")
            return False

        try:
            self.rest_operation(client, issue_key=args.issue_key, points=points)
            print(f"✅ Voted {points} points on {args.issue_key}")
            return True
        except VoteStoryPointsError as e:
            msg = f"❌ Failed to vote on story points: {e}"
            print(msg)
            raise VoteStoryPointsError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to vote on story points.

        Arguments:
            client: JiraClient instance
            **kwargs: Must contain 'issue_key' and 'points'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        points = kwargs["points"]

        # Get issue ID first
        try:
            issue = client.request("GET", f"/rest/api/2/issue/{issue_key}")
            issue_id = issue["id"]
        except Exception as e:
            raise FetchIssueIDError(f"Failed to fetch issue ID for {issue_key}: {e}") from e

        # Submit vote
        payload = {"issueId": issue_id, "vote": points}

        try:
            client.request(
                "PUT",
                "/rest/eausm/latest/planningPoker/vote",
                json_data=payload,
            )
            return {"success": True, "issue_key": issue_key, "points": points}
        except Exception as e:
            raise VoteStoryPointsError(f"Failed to vote on story points: {e}") from e
