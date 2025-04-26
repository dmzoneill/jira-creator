#!/usr/bin/env python
"""
This module provides a function to view user details using a Jira instance.
It retrieves user information based on the provided account ID and displays it in a sorted manner.
If an error occurs during the retrieval process, it catches and handles the GetUserError exception.

The function cli_view_user(jira, args) retrieves information about a specific user from Jira.
It takes two arguments:
- jira (JiraClient): An instance of the JiraClient class used to interact with the Jira API.
- args (dict): A dictionary containing the arguments needed to identify the user. It should include the
'account_id' key representing the unique identifier of the user.

This function may raise exceptions if there are issues with retrieving the user information from Jira.
"""

from argparse import Namespace
from typing import Any, Dict

from exceptions.exceptions import GetUserError
from rest.client import JiraClient


def cli_view_user(jira: JiraClient, args: Namespace) -> Dict[str, Any]:
    """
    Retrieve information about a specific user from Jira.

    Arguments:
    - jira (JiraClient): An instance of the JiraClient class used to interact with the Jira API.
    - args (dict): A dictionary containing the arguments needed to identify the user. It should include the
    'account_id' key representing the unique identifier of the user.

    Exceptions:
    - GetUserError: Raised if there are issues with retrieving the user information from Jira.
    """

    try:
        user = jira.get_user(args.account_id)

        # Keys to be dropped
        keys_to_drop = [
            "self",
            "avatarUrls",
            "ownerId",
            "applicationRoles",
            "groups",
            "expand",
        ]

        # Prepare filtered user data
        filtered_user = {
            key: value for key, value in user.items() if key not in keys_to_drop
        }

        # Print the data in a formatted ASCII table
        print(f"{'Key':<20} {'Value'}")
        print("-" * 40)  # Separator for the table

        for key, value in sorted(filtered_user.items()):
            # Format the value for better readability
            formatted_value = value if isinstance(value, str) else str(value)
            print(f"{key:<20} {formatted_value}")

        return filtered_user
    except GetUserError as e:
        msg = f"❌ Unable to retrieve user: {e}"
        print(msg)
        raise GetUserError(msg) from e
