"""
This module provides a function to view user details using a Jira instance.
It retrieves user information based on the provided account ID and displays it in a sorted manner.
If an error occurs during the retrieval process, it catches and handles the GetUserError exception.
"""

from exceptions.exceptions import GetUserError


def cli_view_user(jira, args):
    """
    Retrieve information about a specific user from Jira.

    Arguments:
    - jira (JiraClient): An instance of the JiraClient class used to interact with the Jira API.
    - args (dict): A dictionary containing the arguments needed to identify the user. It should include the
    'account_id' key representing the unique identifier of the user.

    Exceptions:
    - This function may raise exceptions if there are issues with retrieving the user information from Jira.

    """

    try:
        user = jira.get_user(args.account_id)

        for key in sorted(user.keys()):
            print(f"{key} : {user[key]}")
        return user
    except GetUserError as e:
        msg = f"❌ Unable to retrieve user: {e}"
        print(msg)
        raise GetUserError(msg)
