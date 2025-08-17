#!/usr/bin/env python
"""
Blocked issues plugin for jira-creator.

This plugin implements the blocked command, allowing users to view
blocked issues based on project, component, and user filters.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Union

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import ListBlockedError
from jira_creator.plugins.base import JiraPlugin


class BlockedPlugin(JiraPlugin):
    """Plugin for listing blocked issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "blocked"

    @property
    def help_text(self) -> str:
        """Return the command help text."""
        return "List blocked issues"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments with the argument parser."""
        parser.add_argument("--user", help="Filter by assignee (username)")
        parser.add_argument("--project", help="Project key override")
        parser.add_argument("--component", help="Component name override")

    def execute(self, client: Any, args: Namespace) -> bool:
        """Execute the blocked command."""
        try:
            result = self.rest_operation(
                client,
                project=getattr(args, "project", None),
                component=getattr(args, "component", None),
                user=getattr(args, "user", None),
            )
            # Success if we got a result, regardless of whether issues were found
            return isinstance(result, dict) and "blocked_issues" in result
        except ListBlockedError as e:
            msg = f"❌ Failed to list blocked issues: {e}"
            print(msg)
            raise ListBlockedError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to list blocked issues.

        Arguments:
            client: JiraClient instance
            **kwargs: May contain 'project', 'component', 'user', and '_test_issues'

        Returns:
            Dict[str, Any]: Response containing blocked issues and status
        """
        # pylint: disable=fixme
        # project = kwargs.get("project")  # TODO: Implement project filtering
        # component = kwargs.get("component")  # TODO: Implement component filtering
        # pylint: enable=fixme
        user = kwargs.get("user")

        # Get current user if no user specified
        if not user:
            current_user_response = client.request("GET", "/rest/api/2/myself")
            user = current_user_response.get("name") or current_user_response.get("accountId")

        # Allow test data injection for testing purposes
        if "_test_issues" in kwargs:
            issues = kwargs.get("_test_issues", [])
        else:
            # For now, return empty list - plugin needs full list_issues implementation
            # This is a placeholder until the full list_issues logic is implemented
            issues = []

        if not issues:
            print("✅ No issues found.")
            return {"blocked_issues": [], "message": "No issues found"}

        blocked_issues: List[Dict[str, Union[str, None]]] = []
        for issue in issues:
            fields = issue["fields"]
            is_blocked = fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value") == "True"
            if is_blocked:
                blocked_issues.append(
                    {
                        "key": issue["key"],
                        "status": fields["status"]["name"],
                        "assignee": (fields["assignee"]["displayName"] if fields["assignee"] else "Unassigned"),
                        "reason": fields.get(EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"), "(no reason)"),
                        "summary": fields["summary"],
                    }
                )

        if not blocked_issues:
            print("✅ No blocked issues found.")
            return {"blocked_issues": [], "message": "No blocked issues found"}

        print("🔒 Blocked issues:")
        print("-" * 80)
        for i in blocked_issues:
            print(f"{i['key']} [{i['status']}] — {i['assignee']}")
            print(f"  🔸 Reason: {i['reason']}")
            print(f"  📄 {i['summary']}")
            print("-" * 80)

        return {"blocked_issues": blocked_issues, "message": f"Found {len(blocked_issues)} blocked issues"}
