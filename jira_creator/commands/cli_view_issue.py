#!/usr/bin/env python
"""
This script defines a function cli_view_issue that retrieves and displays information about a Jira issue. It handles
custom fields by replacing their keys with their real names using a helper function from the Jira object. The function
then sorts and prints the issue details. If an exception ViewIssueError is raised during the process, it catches the
exception, prints an error message, and raises the exception again.

Function cli_view_issue:
- View a specific issue in JIRA.
- Arguments:
- jira: A JIRA client object used to interact with the JIRA API.
- args: A dictionary containing the following key:
- issue_key: A string representing the key of the issue to be viewed.
- Exceptions:
- This function may raise exceptions if there are issues with accessing or viewing the specified issue in JIRA.
- Note:
- This function retrieves and displays information about a specific issue in JIRA using the provided JIRA client object.
"""

# pylint: disable=too-many-return-statements

from argparse import Namespace
from typing import Any, Dict

from exceptions.exceptions import ViewIssueError
from rest.client import JiraClient


def cli_view_issue(jira: JiraClient, args: Namespace) -> Any:
    """
    View a specific issue in JIRA.

    Arguments:
    - jira: A JIRA client object used to interact with the JIRA API.
    - args: A dictionary containing the following key:
    - issue_key: A string representing the key of the issue to be viewed.

    Exceptions:
    - This function may raise exceptions if there are issues with accessing or viewing the specified issue in JIRA.

    Note:
    - This function retrieves and displays information about a specific issue in JIRA using the provided JIRA client
    object.
    """
    # Allowed keys for printing
    allowed_keys = [
        "acceptance criteria",
        "blocked",
        "blocked reason",
        "epic link",
        "priority",
        "labels",
        "feature link",
        "flagged",
        "status",
        "summary",
        "updated",
        "subtasks",
        "reporter",
        "ready",
        "release blocker",
        "resolved date",
        "severity",
        "sprint",
        "story points",
        "description",
        "assignee",
    ]

    def format_multiline(value: str) -> str:
        """
        Format multiline values by padding each line to align with the 'Value' column
        which has a width of 30 characters. All lines will start after the 30-character padding.
        """
        lines = value.splitlines()

        # Ensure the first line is aligned after 30 characters
        formatted_lines = [f"{lines[0]:<30}"]  # Format the first line with 30 padding

        # For subsequent lines, add 30 spaces at the beginning of each
        formatted_lines += [f"{' ' * 31}{line}" for line in lines[1:]]

        return "\n".join(formatted_lines)

    def parse_value(value: Any) -> Any:
        """
        Handle different types of values:
        - If it's a dictionary, return 'name' or 'value'.
        - If it's a list, join the items with commas.
        - If it's None, return None.
        - If it's a multiline string, format each line.
        """
        if isinstance(value, dict):
            # Check for 'name' or 'value' field in the dictionary
            if "name" in value:
                return value["name"]
            if "value" in value:
                return value["value"]
            return str(value)
        if isinstance(value, list):
            # Join list items into a single string separated by commas
            return ", ".join(str(item) for item in value)
        if isinstance(value, str):
            # If it's a string, check if it's multiline and format it
            if "\n" in value:
                return format_multiline(value)
        if value is None:
            return None
        return value  # Return other types as they are (e.g., strings, integers, etc.)

    try:
        issue = jira.view_issue(args.issue_key)

        # Create a new dictionary with real names as keys
        updated_issue: Dict[str, Any] = {}

        for key in issue:
            # Check if the key is a custom field
            if "customfield" in key:
                real_name = jira.get_field_name(key)
                updated_issue[real_name] = issue[key]
            else:
                # For non-custom fields, keep the original key
                updated_issue[key] = issue[key]

        # Print the data in a formatted ASCII table
        print(f"{'Key':<30} {'Value'}")
        print("-" * 60)  # Separator for the table

        # Sort the dictionary by keys and print each in a table-like format
        for key, value in sorted(updated_issue.items()):
            # Convert key to lowercase for comparison
            key_lower = key.lower()

            # Check if the key exactly matches the allowed list (case-insensitive)
            if any(key_lower == allowed_key for allowed_key in allowed_keys):
                # Parse the value if it's a JSON string, list, or multiline string
                parsed_value = parse_value(value)

                # Skip printing None or empty values
                if parsed_value is None or parsed_value == "None":
                    continue

                # Print the key and parsed value in a formatted manner
                print(f"{key:<30} {parsed_value}")

        return issue
    except ViewIssueError as e:
        msg = f"❌ Unable to view issue: {e}"
        print(msg)
        raise ViewIssueError(e) from e
