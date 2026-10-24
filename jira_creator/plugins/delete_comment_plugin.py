#!/usr/bin/env python
"""
Delete comment plugin for jira-creator.

This plugin implements the delete-comment command, allowing users to delete
comments from Jira issues by comment ID or by matching body text.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional

from jira_creator.core.plugin_base import JiraPlugin


class DeleteCommentError(Exception):
    """Exception raised when deleting a comment fails."""


class DeleteCommentPlugin(JiraPlugin):
    """Plugin for deleting comments from Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "delete-comment"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Delete a comment from a Jira issue (by ID or by body text)"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Utilities"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return [
            "delete-comment AAP-12345 12345678",
            'delete-comment AAP-12345 --containing "Correction —"',
            "delete-comment AAP-12345 --latest",
            "delete-comment AAP-12345 --all",
        ]

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "DeleteCommentError": DeleteCommentError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument(
            "comment_id",
            nargs="?",
            default=None,
            help="Comment ID (from Jira). Omit if using --containing.",
        )
        parser.add_argument(
            "--containing",
            metavar="TEXT",
            default=None,
            help="Delete the first comment whose body contains this text (case-sensitive).",
        )
        parser.add_argument(
            "--latest",
            action="store_true",
            help="Delete the most recent comment on the issue.",
        )
        parser.add_argument(
            "--all",
            dest="delete_all",
            action="store_true",
            help="Delete all comments on the issue.",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the delete-comment command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            if args.delete_all:
                count = self._delete_all_comments(client, args.issue_key)
                print(f"✅ Deleted {count} comment(s) from {args.issue_key}")
                return True

            comment_id = args.comment_id
            if args.latest:
                comment_id = self._find_latest_comment_id(client, args.issue_key)
                if not comment_id:
                    raise DeleteCommentError(f"No comments found on {args.issue_key}")
            elif args.containing:
                comment_id = self._find_comment_id_by_body(client, args.issue_key, args.containing)
                if not comment_id:
                    raise DeleteCommentError(f"No comment containing {args.containing!r} found on {args.issue_key}")
            elif not comment_id:
                raise DeleteCommentError("Provide comment_id, or --containing TEXT, or --latest, or --all")

            self.rest_operation(client, issue_key=args.issue_key, comment_id=comment_id)
            print(f"✅ Comment {comment_id} deleted from {args.issue_key}")
            return True
        except DeleteCommentError as e:
            print(f"❌ Failed to delete comment: {e}")
            raise

    def rest_operation(self, client: Any, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Perform the REST API operation to delete a comment.

        Arguments:
            client: JiraClient instance
            **kwargs: Must contain 'issue_key' and 'comment_id'

        Returns:
            Optional[Dict]: API response (often None for 204 No Content)
        """
        issue_key = kwargs["issue_key"]
        comment_id = kwargs["comment_id"]

        path = f"/rest/api/2/issue/{issue_key}/comment/{comment_id}"
        return client.request("DELETE", path)

    def _find_latest_comment_id(self, client: Any, issue_key: str) -> Optional[str]:
        """Return the ID of the most recent comment (last in list; API often returns newest last)."""
        path = f"/rest/api/2/issue/{issue_key}/comment"
        response = client.request("GET", path)
        if not response:
            return None
        comments = response.get("comments", [])
        if not comments:
            return None
        # Jira typically returns oldest first; last is newest
        last = comments[-1]
        cid = last.get("id")
        return str(cid) if cid is not None else None

    def _delete_all_comments(self, client: Any, issue_key: str) -> int:
        """Delete every comment on the issue. Returns number deleted."""
        path = f"/rest/api/2/issue/{issue_key}/comment"
        response = client.request("GET", path)
        if not response:
            return 0
        comments = response.get("comments", [])
        count = 0
        for comment in comments:
            cid = comment.get("id")
            if cid is not None:
                self.rest_operation(client, issue_key=issue_key, comment_id=str(cid))
                count += 1
        return count

    def _find_comment_id_by_body(self, client: Any, issue_key: str, containing: str) -> Optional[str]:
        """Get comments for the issue and return the ID of the first whose body contains the text."""
        path = f"/rest/api/2/issue/{issue_key}/comment"
        response = client.request("GET", path)
        if not response:
            return None
        comments = response.get("comments", [])
        for comment in comments:
            body = (comment.get("body") or "") if isinstance(comment.get("body"), str) else ""
            if containing in body:
                cid = comment.get("id")
                return str(cid) if cid is not None else None
        return None
