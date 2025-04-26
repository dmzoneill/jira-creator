#!/usr/bin/env python
"""
A function to retrieve and list sprints from a Jira board using the provided Jira instance and arguments.

Parameters:
- jira (Jira): An instance of the Jira class to interact with Jira API.
- args (Namespace): A namespace object containing arguments including 'board_id' for the board to retrieve sprints from.

Returns:
- List[str]: A list of sprints retrieved from the specified Jira board.

Raises:
- Exception: If there is an error while retrieving the sprints, an exception is raised with an error message.

Prints:
- The retrieved sprints are printed in a formatted manner.
- Success message if sprints are retrieved successfully.
- Error message if there is a failure in retrieving sprints.
"""

from argparse import Namespace
from typing import List

from rest.client import JiraClient


def cli_list_sprints(jira: JiraClient, args: Namespace) -> List[str]:
    """
    Retrieve and display a list of sprints for a specified Jira board.

    Arguments:
    - jira (JIRA): An instance of the JIRA class used to interact with the Jira API.
    - args (Namespace): A namespace object containing parsed command-line arguments.

    Return:
    - List[str]: A list of sprint names retrieved from the specified Jira board.

    Side Effects:
    - Prints the list of sprints retrieved from the specified Jira board.

    Exceptions:
    - If an error occurs during the retrieval of sprints, an exception is raised with a descriptive error message.
    """

    try:
        board_id: str = jira.board_id if jira.board_id else args.board_id
        response: List[str] = jira.list_sprints(board_id)
        for sprint in response:
            print(f"    - {sprint}")

        print("✅ Successfully retrieved sprints")
        return response
    except Exception as e:
        msg: str = f"❌ Failed to retrieve sprints: {e}"
        print(msg)
        raise
