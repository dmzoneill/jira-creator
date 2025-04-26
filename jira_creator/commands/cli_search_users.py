#!/usr/bin/env python
"""
This script defines a function 'cli_search_users' that takes a Jira instance and search arguments as input parameters.
It attempts to search for users using the provided query and prints the user details if found.
If no users are found, it prints a warning message. If an error occurs during the search, it raises a SearchUsersError
exception.

Function cli_search_users:
- Search for users in Jira based on the provided query.
- Arguments:
- jira (JIRA): An instance of the JIRA client.
- args (Namespace): A namespace object containing the query to search for users.
- Return:
- Union[List[Dict[str, Any]], bool]: A list of dictionaries representing the found users if any, else False.
- Exceptions:
- This function may raise an exception if there is an issue with searching for users in Jira.
"""

from argparse import Namespace
from typing import Any, Dict, List, Union

from exceptions.exceptions import SearchUsersError
from rest.client import JiraClient


def cli_search_users(
    jira: JiraClient, args: Namespace
) -> Union[List[Dict[str, Any]], bool]:
    """
    Search for users in Jira based on the provided query.

    Arguments:
    - jira (JIRA): An instance of the JIRA client.
    - args (Namespace): A namespace object containing the query to search for users.

    Return:
    - Union[List[Dict[str, Any]], bool]: A list of dictionaries representing the found users if any, else False.

    Exceptions:
    - This function may raise an exception if there is an issue with searching for users in Jira.
    """

    try:
        users: List[Dict[str, Any]] = jira.search_users(args.query)

        if not users:
            print("⚠️ No users found.")
            return False

        for user in users:
            print("🔹 User:")
            for key in sorted(user.keys()):
                print(f"  {key}: {user[key]}")
            print("")
        return users
    except SearchUsersError as e:
        msg = f"❌ Unable to search users: {e}"
        print(msg)
        raise SearchUsersError(e) from e
