#!/usr/bin/env python
"""
Set the epic for a story in Jira.

This script defines a function 'cli_set_story_epic' that sets the epic for a story in Jira. It takes two arguments:
- jira: An instance of the Jira client.
- args: A namespace containing 'issue_key' (str) and 'epic_key' (str) attributes.

Returns:
- bool: True if the epic was successfully set for the story.

Exceptions:
- SetStoryEpicError: Raised when there is an error setting the epic for the story.

Side Effects:
- Prints a success message if the epic is set successfully.
- Prints an error message if setting the epic fails.
"""
from argparse import Namespace

from exceptions.exceptions import SetStoryEpicError
from rest.client import JiraClient


def cli_set_story_epic(jira: JiraClient, args: Namespace) -> bool:
    """
    Set the epic for a story in Jira.

    Arguments:
    - jira: An instance of the Jira client.
    - args: A namespace containing the following attributes:
    - issue_key (str): The key of the story to update.
    - epic_key (str): The key of the epic to set for the story.

    Return:
    - bool: True if the epic was successfully set for the story.

    Exceptions:
    - SetStoryEpicError: Raised when there is an error setting the epic for the story.

    Side Effects:
    - Prints a success message if the epic is set successfully.
    - Prints an error message if setting the epic fails.
    """

    if not hasattr(args, "issue_key") or not hasattr(args, "epic_key"):
        raise ValueError("Arguments must contain 'issue_key' and 'epic_key'.")

    if not isinstance(args.issue_key, str) or not isinstance(args.epic_key, str):
        raise TypeError("Both 'issue_key' and 'epic_key' must be strings.")

    try:
        jira.set_story_epic(args.issue_key, args.epic_key)
        print(f"✅ Story's epic set to '{args.epic_key}'")
        return True
    except SetStoryEpicError as e:
        msg = f"❌ Failed to set epic for issue '{args.issue_key}': {str(e)}"
        print(msg)
        raise SetStoryEpicError(msg) from e
    except Exception as e:
        msg = f"❌ An unexpected error occurred: {str(e)}"
        print(msg)
        raise RuntimeError(msg) from e
