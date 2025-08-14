#!/usr/bin/env python
"""
List issues plugin for jira-creator.

This plugin implements the list-issues command, allowing users to list
and filter Jira issues with various criteria.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.view_helpers import format_and_print_rows, massage_issue_list
from jira_creator.exceptions.exceptions import ListIssuesError
from jira_creator.plugins.base import JiraPlugin


class ListIssuesPlugin(JiraPlugin):
    """Plugin for listing Jira issues with filtering options."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "list-issues"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "List issues from a project with various filters"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument(
            "-p",
            "--project",
            help="Project key (uses JIRA_PROJECT_KEY env if not specified)",
            default=None,
        )
        parser.add_argument("-c", "--component", help="Filter by component name", default=None)
        parser.add_argument("-a", "--assignee", help="Filter by assignee username", default=None)
        parser.add_argument("-r", "--reporter", help="Filter by reporter username", default=None)
        parser.add_argument("-s", "--status", help="Filter by status", default=None)
        parser.add_argument("--summary", help="Filter by summary containing text", default=None)
        parser.add_argument("--blocked", action="store_true", help="Show only blocked issues")
        parser.add_argument("--unblocked", action="store_true", help="Show only unblocked issues")
        parser.add_argument("--sort", help="Sort by field(s), comma-separated", default="key")
        parser.add_argument(
            "-m",
            "--max-results",
            type=int,
            default=100,
            help="Maximum number of results (default: 100)",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the list-issues command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Build JQL query from arguments
            jql = self._build_jql_query(args)

            if not jql:
                print("❌ No project specified. Use --project or set JIRA_PROJECT_KEY")
                return False

            # Get issues
            issues = self.rest_operation(client, jql=jql, max_results=args.max_results, order_by=args.sort)

            if not issues:
                print("📭 No issues found matching your criteria")
                return True

            # Process and display results
            headers, rows = massage_issue_list(args, issues)
            format_and_print_rows(rows, headers, client)

            print(f"\n📊 Found {len(issues)} issue(s)")
            return True

        except ListIssuesError as e:
            msg = f"❌ Failed to list issues: {e}"
            print(msg)
            raise ListIssuesError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform the REST API operation to list issues.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'jql', 'max_results', and 'order_by'

        Returns:
            List[Dict[str, Any]]: List of issue data
        """
        jql = kwargs["jql"]
        max_results = kwargs.get("max_results", 100)
        order_by = kwargs.get("order_by", "key")

        # Get all fields that should be included
        fields_to_include = [
            "key",
            "summary",
            "status",
            "assignee",
            "reporter",
            "priority",
            "issuetype",
            "created",
            "updated",
            "components",
        ]

        # Add custom fields from environment variables
        sprint_field = EnvFetcher.get("JIRA_SPRINT_FIELD", "")
        if sprint_field:
            fields_to_include.append(sprint_field)

        story_points_field = EnvFetcher.get("JIRA_STORY_POINTS_FIELD", "")
        if story_points_field:
            fields_to_include.append(story_points_field)

        blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD", "")
        if blocked_field:
            fields_to_include.append(blocked_field)

        # Build search parameters
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields_to_include),
        }

        # Add ordering if specified
        if order_by:
            params["orderBy"] = order_by

        # Perform the search
        path = "/rest/api/2/search"
        response = client.request("GET", path, params=params)

        return response.get("issues", [])

    def _build_jql_query(self, args: Namespace) -> str:
        """Build JQL query from command arguments."""
        # pylint: disable=too-many-branches
        conditions = []

        # Project filter
        project = args.project or EnvFetcher.get("JIRA_PROJECT_KEY", "")
        if project:
            conditions.append(f"project = {project}")
        else:
            return ""  # No project specified

        # Component filter
        if args.component:
            component = args.component or EnvFetcher.get("JIRA_COMPONENT_NAME", "")
            if component:
                conditions.append(f"component = '{component}'")

        # Status filter
        if args.status:
            conditions.append(f"status = '{args.status}'")

        # Assignee/Reporter filter (reporter takes precedence)
        if args.reporter:
            conditions.append(f"reporter = '{args.reporter}'")
        elif args.assignee:
            conditions.append(f"assignee = '{args.assignee}'")

        # Summary filter
        if args.summary:
            conditions.append(f"summary ~ '{args.summary}'")

        # Blocked/Unblocked filter
        if args.blocked and args.unblocked:
            # Both specified, don't filter
            pass
        elif args.blocked:
            blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD", "")
            if blocked_field:
                conditions.append(f"{blocked_field} = 'True'")
        elif args.unblocked:
            blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD", "")
            if blocked_field:
                conditions.append(f"({blocked_field} != 'True' OR {blocked_field} IS EMPTY)")

        return " AND ".join(conditions)
