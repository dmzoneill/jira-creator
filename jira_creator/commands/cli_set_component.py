#!/usr/bin/env python
"""
A function to set a component for a Jira issue using the provided Jira instance and command line arguments.

Parameters:
- jira (Jira): An instance of the Jira class.
- args (Namespace): Command line arguments containing component_name and issue_key.

Returns:
- response: Response from setting the component for the issue.

Raises:
- SetComponentError: If an error occurs while setting the component, an exception of type SetComponentError is raised.
"""
from exceptions.exceptions import SetComponentError


def cli_set_component(jira, args):
    """
    Set a component for a JIRA issue using the provided JIRA client.

    Arguments:
    - jira (JIRA): An instance of the JIRA client.
    - args (Namespace): A namespace containing the following attributes:
    - component_name (str): The name of the component to set.
    - issue_key (str): The key of the issue to set the component for.

    Return:
    - dict: The response from setting the component for the JIRA issue.

    Exceptions:
    - SetComponentError: Raised when an error occurs while setting the component.

    Side Effects:
    - Prints a success message if the component is set successfully.
    - Prints an error message if setting the component fails.
    """
    component_name = args.component_name
    issue_key = args.issue_key
    try:
        response = jira.set_component(issue_key, component_name)
        print(f"✅ Component '{component_name}' set for issue '{issue_key}'")
        return response
    except SetComponentError as e:
        msg = f"❌ {e}"
        print(msg)
        raise SetComponentError(e) from e
