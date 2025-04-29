#!/usr/bin/env python
"""
This module provides a function to set a project for a Jira issue using the given Jira instance and command-line
arguments.

The 'cli_set_project' function takes two arguments:
- jira: A Jira instance.
- args: Command-line arguments containing 'issue_key' and 'project_key'.

If the project is set successfully, it prints a success message and returns the response.
If there is an error while setting the project, it catches the 'SetProjectError' exception, prints an error message,
and re-raises the exception.

Exceptions:
- SetProjectError: Raised when an error occurs while setting the project.

Example usage:
cli_set_project(jira_instance, args)
"""
from exceptions.exceptions import SetProjectError


def cli_set_project(jira, args):
    """
    Set a project for a Jira issue using the provided Jira client.

    Arguments:
    - jira (JiraClient): An instance of the Jira client used to interact with the Jira API.
    - args (Namespace): A namespace object containing the following attributes:
    - issue_key (str): The key of the Jira issue for which the project needs to be set.
    - project_key (str): The key of the project to set for the Jira issue.

    Return:
    - dict: A response from the Jira API after setting the project for the specified issue.

    Exceptions:
    - SetProjectError: Raised if there is an error while setting the project for the issue.

    Side Effects:
    - Prints a success message if the project is set successfully.
    - Prints an error message if there is an issue setting the project and raises a SetProjectError.
    """
    issue_key = args.issue_key
    project_key = args.project_key
    try:
        response = jira.set_project(issue_key, project_key)
        print(f"✅ Project '{project_key}' set for issue '{issue_key}'")
        return response
    except SetProjectError as e:
        msg = f"❌ {e}"
        print(msg)
        raise SetProjectError(e) from e
