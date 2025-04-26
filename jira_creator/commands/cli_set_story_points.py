#!/usr/bin/env python
"""
This module provides a function for setting story points in Jira using the command-line interface (CLI).

The 'cli_set_story_points' function takes two arguments:
- jira: A Jira connection object.
- args: A dictionary containing the arguments passed in the command-line interface. It should contain a key 'points'
representing the story points to be set for the Jira issue.

The function attempts to convert the story points provided in the arguments to an integer. If successful, it calls the
'set_story_points' method of the Jira client to set the story points for a specific issue identified by the issue key
provided in the arguments.

If the conversion to an integer fails, an error message is displayed, and the function returns False. If setting the
story points fails due to a 'SetStoryPointsError', the function raises the exception with an error message.

The function provides feedback messages on the success or failure of setting the story points.

Note: The 'SetStoryPointsError' is imported from 'exceptions.exceptions'.
"""

from argparse import Namespace

from exceptions.exceptions import SetStoryPointsError
from rest.client import JiraClient


def cli_set_story_points(jira: JiraClient, args: Namespace) -> bool:
    """
    Set the story points for a Jira issue in the command-line interface.

    Arguments:
    - jira: A Jira connection object.
    - args: A dictionary containing the arguments passed in the command-line interface.
    It should contain a key 'points' representing the story points to be set for the Jira issue.

    Return:
    - False if the provided story points are not an integer.

    Exceptions:
    - SetStoryPointsError: Raised when there is an error setting the story points for the Jira issue.
    """

    try:
        points = int(args.points)
    except (ValueError, KeyError):
        print("❌ Points must be an integer.")
        return False

    try:
        jira.set_story_points(args.issue_key, points)
        print(f"✅ Set {points} story points on {args.issue_key}")
        return True
    except SetStoryPointsError as e:
        msg = f"❌ Failed to set story points: {e}"
        print(msg)
        raise SetStoryPointsError(e) from e
