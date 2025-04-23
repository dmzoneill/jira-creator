"""
This script defines a function 'cli_search_users' that takes a Jira instance and search arguments as input parameters.
It attempts to search for users using the provided query and prints the user details if found.
If no users are found, it prints a warning message. If an error occurs during the search, it raises a SearchUsersError
exception.
"""

from exceptions.exceptions import SearchUsersError


def cli_search_users(jira, args):
    """
    Search for users in Jira based on the provided query.

    Arguments:
    - jira (JIRA): An instance of the JIRA client.
    - args (Namespace): A namespace object containing the query to search for users.

    Exceptions:
    - This function may raise an exception if there is an issue with searching for users in Jira.

    """

    try:
        users = jira.search_users(args.query)

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
        raise SearchUsersError(msg)
