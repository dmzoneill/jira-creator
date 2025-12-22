#!/usr/bin/env python
"""
Search plugin for jira-creator.

This plugin implements the search command, allowing users to search
for Jira issues using JQL (Jira Query Language).
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.view_helpers import format_and_print_rows, massage_issue_list


class SearchError(Exception):
    """Exception raised for search-related errors."""


class SearchPlugin(JiraPlugin):
    """Plugin for searching Jira issues using JQL."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "search"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Search for issues using JQL (Jira Query Language)"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Search & View"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ['search "project = AAP AND status = Open"', 'search "assignee = currentUser()"']

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "SearchError": SearchError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("jql", help="JQL query string (e.g., 'project = ABC AND status = Open')")
        parser.add_argument(
            "-m",
            "--max-results",
            type=int,
            default=50,
            help="Maximum number of results to return (default: 50)",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the search command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Perform the search
            results = self.rest_operation(client, jql=args.jql, max_results=args.max_results)

            if not results:
                print("📭 No issues found matching your query")
                return True

            # Process and display results
            headers, rows = massage_issue_list(args, results)
            format_and_print_rows(rows, headers, client)

            print(f"\n📊 Found {len(results)} issue(s)")
            return True

        except SearchError as e:
            msg = f"❌ Search failed: {e}"
            print(msg)
            raise SearchError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform the REST API operation to search for issues.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'jql' and 'max_results'

        Returns:
            List[Dict[str, Any]]: List of issue data
        """
        jql = kwargs["jql"]
        max_results = kwargs.get("max_results", 50)

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

        # Build the search parameters
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields_to_include),
        }

        # Perform the search
        path = "/rest/api/2/search"
        response = client.request("GET", path, params=params)

        # Extract issues from response
        return response.get("issues", [])
