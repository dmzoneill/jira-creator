#!/usr/bin/env python
"""
List blocked plugin for jira-creator.

This plugin implements the list-blocked command, allowing users to view
all issues that are currently blocked, with detailed blocker information.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import ListBlockedError


class ListBlockedPlugin(JiraPlugin):
    """Plugin for listing blocked issues with blocker details."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "list-blocked"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "List all blocked issues with blocker details"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Search & View"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["list-blocked", "list-blocked --project AAP"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("--project", help="Filter by project key")
        parser.add_argument("--assignee", help="Filter by assignee username")
        parser.add_argument("--status", help="Filter by status (e.g., 'In Progress')")
        parser.add_argument("--show-blockers", action="store_true", help="Show blocker issue details")
        parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the list-blocked command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Build JQL query
            jql = self._build_jql(args)

            # Search for issues
            result = self.rest_operation(client, jql=jql)
            issues = result.get("issues", [])

            if not issues:
                print("No blocked issues found.")
                return True

            # Process and display results
            blocked_issues = self._process_issues(client, issues, args.show_blockers)

            if args.output == "json":
                import json

                print(json.dumps(blocked_issues, indent=2))
            else:
                self._display_text(blocked_issues, args.show_blockers)

            return True

        except ListBlockedError as e:
            print(f"❌ Failed to list blocked issues: {e}")
            raise

    def _build_jql(self, args: Namespace) -> str:
        """
        Build JQL query for blocked issues.

        Arguments:
            args: Parsed command arguments

        Returns:
            str: JQL query string
        """
        # Base query for issues with blockers
        # Issues are blocked if they have inward "Blocks" links
        jql_parts = []

        # Project filter
        if args.project:
            project = args.project
        else:
            project = EnvFetcher.get("JIRA_PROJECT_KEY", default="")

        if project:
            jql_parts.append(f'project = "{project}"')

        # Status filter (default to non-closed)
        if args.status:
            jql_parts.append(f'status = "{args.status}"')
        else:
            # Exclude closed/done issues
            jql_parts.append("status NOT IN (Closed, Done, Resolved)")

        # Assignee filter
        if args.assignee:
            jql_parts.append(f'assignee = "{args.assignee}"')

        # Issues with blockers (has inward "Blocks" links)
        jql_parts.append('issueFunction in linkedIssuesOf("project = *", "is blocked by")')

        jql = " AND ".join(jql_parts)
        jql += " ORDER BY priority DESC, created ASC"

        return jql

    # pylint: disable=unused-argument
    def _process_issues(self, client: Any, issues: List[Dict], show_blockers: bool) -> List[Dict]:
        """
        Process issues and optionally fetch blocker details.

        Arguments:
            client: JiraClient instance
            issues: List of issue data from search
            show_blockers: Whether to fetch blocker details

        Returns:
            List of processed issue dictionaries
        """
        processed = []

        for issue in issues:
            fields = issue.get("fields", {})
            issue_key = issue.get("key")

            issue_data = {
                "key": issue_key,
                "summary": fields.get("summary", ""),
                "status": fields.get("status", {}).get("name", ""),
                "priority": fields.get("priority", {}).get("name", ""),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
            }

            # Get blocker information from issue links
            if show_blockers:
                blockers = self._get_blockers(fields)
                issue_data["blockers"] = blockers

            processed.append(issue_data)

        return processed

    def _get_blockers(self, fields: Dict) -> List[Dict]:
        """
        Extract blocker information from issue links.

        Arguments:
            fields: Issue fields dictionary

        Returns:
            List of blocker dictionaries
        """
        blockers = []
        issue_links = fields.get("issuelinks", [])

        for link in issue_links:
            # Inward links are issues that block this one
            if link.get("type", {}).get("inward") == "is blocked by":
                inward_issue = link.get("inwardIssue", {})
                if inward_issue:
                    blocker = {
                        "key": inward_issue.get("key"),
                        "summary": inward_issue.get("fields", {}).get("summary", ""),
                        "status": inward_issue.get("fields", {}).get("status", {}).get("name", ""),
                    }
                    blockers.append(blocker)

        return blockers

    def _display_text(self, issues: List[Dict], show_blockers: bool) -> None:
        """
        Display issues in text format.

        Arguments:
            issues: List of processed issue dictionaries
            show_blockers: Whether to show blocker details
        """
        print(f"\n🚫 Blocked Issues ({len(issues)} found)")
        print("=" * 80)

        for issue in issues:
            print(f"\n{issue['key']}: {issue['summary']}")
            print(f"  Status: {issue['status']}")
            print(f"  Priority: {issue['priority']}")
            print(f"  Assignee: {issue['assignee']}")

            if show_blockers and issue.get("blockers"):
                print("  Blocked by:")
                for blocker in issue["blockers"]:
                    print(f"    - {blocker['key']}: {blocker['summary']} [{blocker['status']}]")

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to search for issues.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'jql'

        Returns:
            Dict[str, Any]: API response with issues
        """
        jql = kwargs["jql"]
        path = "/rest/api/2/search"

        # Request specific fields including issue links
        params = {
            "jql": jql,
            "fields": "summary,status,priority,assignee,issuelinks",
            "maxResults": 100,
        }

        return client.request("GET", path, params=params)
