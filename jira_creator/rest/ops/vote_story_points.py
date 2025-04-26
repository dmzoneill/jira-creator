#!/usr/bin/env python
"""
This module provides functionality to vote on story points for a JIRA issue via the JIRA API. It includes error handling
for issues related to fetching the issue ID and submitting the vote, utilizing custom exceptions for clarity.

Functionality:
- vote_story_points(request_fn, issue_key, points): Submits a vote for story points on a specified JIRA issue.

Parameters:
- request_fn (function): A callable for making HTTP requests to the JIRA API.
- issue_key (str): The unique identifier of the JIRA issue for which story points are being voted.
- points (int): The number of story points to be voted for the issue.

Custom Exceptions:
- FetchIssueIDError: Raised when unable to retrieve the ID of the specified JIRA issue.
- VoteStoryPointsError: Raised when there is an error in submitting the vote for story points.

Side Effects:
- Initiates an HTTP request to obtain the JIRA issue ID.
- Outputs error messages in case of failures during the fetching or voting process.
- Confirms successful voting with a message if the operation completes successfully.

Note:
The module is designed to facilitate the voting process on story points for JIRA issues, leveraging a provided request
function to interact with the JIRA API.
"""

from typing import Any, Callable

from exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError


def vote_story_points(
    request_fn: Callable[[str, str, dict], Any], issue_key: str, points: int
) -> None:
    """
    Vote story points for a given Jira issue.

    Arguments:
    - request_fn (Callable[[str, str, dict], Any]): A function used to make HTTP requests.
    - issue_key (str): The key of the Jira issue to vote story points for.
    - points (int): The number of story points to vote for the issue.

    Exceptions:
    - FetchIssueIDError: Raised when there is an issue fetching the ID of the Jira issue.
    - VoteStoryPointsError: Raised when there is an error in voting for story points.

    Side Effects:
    - Makes an HTTP request to fetch the Jira issue ID.
    - Prints an error message if there is a failure in fetching the issue ID.
    - Prints a success message after voting for story points.

    Note:
    This function is responsible for voting story points for a specific Jira issue by using the provided request
    function to fetch the issue ID and then submitting the vote with the specified points.
    """

    try:
        issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}", {})
        issue_id = issue["id"]
    except FetchIssueIDError as e:
        msg = f"❌ Failed to fetch issue ID for {issue_key}: {e}"
        print(msg)
        raise FetchIssueIDError(e) from e

    payload = {"issueId": issue_id, "vote": points}

    try:
        response = request_fn(
            "PUT",
            "/rest/eausm/latest/planningPoker/vote",
            payload,
        )
        if response.status_code != 200:
            raise VoteStoryPointsError(
                f"JIRA API error ({response.status_code}): {response.text}"
            )
        print(f"✅ Voted {points} story points on issue {issue_key}")
    except (VoteStoryPointsError, VoteStoryPointsError) as e:
        msg = f"❌ Failed to vote on story points: {e}"
        print(msg)
        raise VoteStoryPointsError(e) from e
