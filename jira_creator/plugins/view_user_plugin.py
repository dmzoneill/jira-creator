#!/usr/bin/env python
"""
View user plugin for jira-creator.

This plugin implements the view-user command, allowing users to view
detailed information about a Jira user.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import GetUserError
from jira_creator.plugins.base import JiraPlugin


class ViewUserPlugin(JiraPlugin):
    """Plugin for viewing Jira user details."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "view-user"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "View detailed information about a Jira user"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("account_id", help="The user's account ID or username")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the view-user command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Get user details
            user_data = self.rest_operation(client, account_id=args.account_id)

            # Display user information
            self._display_user_details(user_data)

            return True

        except GetUserError as e:
            msg = f"❌ Failed to get user details: {e}"
            print(msg)
            raise GetUserError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to get user details.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'account_id'

        Returns:
            Dict[str, Any]: User data
        """
        account_id = kwargs["account_id"]

        # Try to get user by account ID first
        try:
            path = f"/rest/api/2/user?accountId={account_id}"
            return client.request("GET", path)
        except Exception:  # pylint: disable=broad-exception-caught
            # Fallback to username
            path = f"/rest/api/2/user?username={account_id}"
            return client.request("GET", path)

    def _display_user_details(self, user: Dict[str, Any]) -> None:
        """Display detailed user information."""
        # Filter out unnecessary fields
        keys_to_drop = [
            "self",
            "avatarUrls",
            "ownerId",
            "applicationRoles",
            "groups",
            "expand",
        ]

        # Prepare filtered data
        filtered_user = {k: v for k, v in user.items() if k not in keys_to_drop and v is not None}

        # Display header
        print(f"\n👤 User Details: {user.get('displayName', 'Unknown')}")
        print("=" * 50)

        # Display fields in a nice format
        for key, value in sorted(filtered_user.items()):
            # Format the key nicely
            formatted_key = key.replace("_", " ").replace("-", " ").title()

            # Handle different value types
            if isinstance(value, bool):
                value_str = "Yes" if value else "No"
            elif isinstance(value, list):
                value_str = ", ".join(str(v) for v in value) if value else "None"
            else:
                value_str = str(value)

            print(f"{formatted_key:.<25} {value_str}")

        print("=" * 50)
