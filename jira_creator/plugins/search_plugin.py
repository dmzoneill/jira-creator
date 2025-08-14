#!/usr/bin/env python
"""
Search plugin for jira-creator.

This plugin implements the search command, allowing users to search
for Jira issues using JQL (Jira Query Language).
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.view_helpers import format_and_print_rows, massage_issue_list
from jira_creator.exceptions.exceptions import SearchError
from jira_creator.plugins.base import JiraPlugin


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
            massaged_issues = massage_issue_list(results, client)
            format_and_print_rows(massaged_issues, [], client)

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

        # Build the search parameters
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "key,summary,status,assignee,priority,issuetype,created,updated",
        }

        # Perform the search
        path = "/rest/api/2/search"
        response = client.request("GET", path, params=params)

        # Extract issues from response
        return response.get("issues", [])
