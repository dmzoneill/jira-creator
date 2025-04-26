#!/usr/bin/env python
"""
This script defines a function 'cli_vote_story_points' that allows users to vote on story points in a Jira issue. The
function takes two arguments: 'jira' (representing a Jira instance) and 'args' (containing issue key and points to
vote). It attempts to convert the points to an integer and then calls the 'vote_story_points' method on the Jira
instance. If successful, it prints a success message. If an error occurs, it prints an error message and raises a
'VoteStoryPointsError' exception.

Function 'cli_vote_story_points':
- Validates and converts the story points provided as input to an integer.
- Arguments:
- jira: the Jira object used for interaction.
- args: a dictionary containing the arguments passed from the command-line interface.
- args.points: a string representing the story points to be converted to an integer.
- Return:
- False if the provided story points cannot be converted to an integer.
- Exceptions:
- ValueError: Raised when the provided story points cannot be converted to an integer.
"""

from argparse import Namespace

from exceptions.exceptions import VoteStoryPointsError
from rest.client import JiraClient


def cli_vote_story_points(jira: JiraClient, args: Namespace) -> bool:
    """
    This function validates and converts the story points provided as input to an integer.

    Arguments:
    - jira: the Jira object used for interaction.
    - args: a dictionary containing the arguments passed from the command-line interface.
    - args.points: a string representing the story points to be converted to an integer.

    Return:
    - False if the provided story points cannot be converted to an integer.

    Exceptions:
    - ValueError: Raised when the provided story points cannot be converted to an integer.
    - VoteStoryPointsError: Raised when there is an error while voting on story points.
    """

    try:
        points = int(args.points)
    except ValueError:
        print("❌ Story points must be an integer.")
        return False

    try:
        jira.vote_story_points(args.issue_key, points)
        print(f"✅ Voted {points} points on {args.issue_key}")
        return True
    except VoteStoryPointsError as e:
        msg = f"❌ Failed to vote on story points: {e}"
        print(msg)
        raise VoteStoryPointsError(e) from e
