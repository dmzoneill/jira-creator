#!/usr/bin/env python
"""
This module contains a function to retrieve sprint data from JIRA.

The cli_get_sprint function takes two arguments:
- jira: An object representing the JIRA instance.
- _: A placeholder for additional arguments (not used in this function).

It calls the get_sprint method on the jira object to fetch sprint data, prints "success" to the console, and returns
the response obtained from JIRA.
"""


def cli_get_sprint(jira, _):
    """
    Print the current active sprint.

    Arguments:
    - self: The object instance.

    Return:
    - The result the current active sprint.
    """
    response = jira.get_sprint()
    print(response["values"][0]["name"])
    return response
