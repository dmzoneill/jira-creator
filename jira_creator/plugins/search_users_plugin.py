#!/usr/bin/env python
"""
Search users plugin for jira-creator.

This plugin implements the search-users command, allowing users to search
for Jira users by name or email.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.exceptions.exceptions import SearchUsersError
from jira_creator.plugins.base import JiraPlugin


class SearchUsersPlugin(JiraPlugin):
    """Plugin for searching Jira users."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "search-users"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Search for Jira users by name or email"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("query", help="Search query (name or email)")
        parser.add_argument(
            "-m",
            "--max-results",
            type=int,
            default=50,
            help="Maximum number of results (default: 50)",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the search-users command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Search for users
            users = self.rest_operation(client, query=args.query, max_results=args.max_results)

            if not users:
                print("📭 No users found matching your query")
                return True

            # Display results
            print(f"\n👥 Found {len(users)} user(s):")
            print("=" * 60)

            for user in users:
                self._display_user(user)

            return True

        except SearchUsersError as e:
            msg = f"❌ Failed to search users: {e}"
            print(msg)
            raise SearchUsersError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform the REST API operation to search for users.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'query' and 'max_results'

        Returns:
            List[Dict[str, Any]]: List of user data
        """
        query = kwargs["query"]
        max_results = kwargs.get("max_results", 50)

        # Search for users
        path = "/rest/api/2/user/search"
        params = {"query": query, "maxResults": max_results}

        return client.request("GET", path, params=params)

    def _display_user(self, user: Dict[str, Any]) -> None:
        """Display user information."""
        name = user.get("name", "N/A")
        display_name = user.get("displayName", "N/A")
        email = user.get("emailAddress", "N/A")
        active = "Active" if user.get("active", False) else "Inactive"

        print(f"\n  Username: {name}")
        print(f"  Name: {display_name}")
        print(f"  Email: {email}")
        print(f"  Status: {active}")
        print("-" * 60)
