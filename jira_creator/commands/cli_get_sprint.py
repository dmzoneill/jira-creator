#!/usr/bin/env python
"""
This module contains a function to retrieve sprint data from JIRA.

The cli_get_sprint function takes two arguments:
- jira: An object representing the JIRA instance.
- _: A placeholder for additional arguments (not used in this function).

It calls the get_sprint method on the jira object to fetch sprint data, prints "success" to the console, and returns
the response obtained from JIRA.

The cli_get_sprint function prints the name of the current active sprint fetched from JIRA and returns the response.

Function cli_get_sprint:
- Arguments:
- jira: The JIRA instance.
- Returns:
- The result of the current active sprint.
"""

from argparse import Namespace
from typing import Any, Dict

from rest.client import JiraClient


def cli_get_sprint(jira: JiraClient, _: Namespace) -> Dict[str, Any]:
    """
    Print the current active sprint.

    Arguments:
    - jira: The JIRA instance.

    Return:
    - The result of the current active sprint.
    """
    response = jira.get_sprint()
    print(response["values"][0]["name"])
    return response
