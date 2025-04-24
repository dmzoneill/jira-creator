#!/usr/bin/env python
"""
This module provides a function to vote on story points for a JIRA issue. It handles fetching the issue ID,
constructing the payload, and making the API request to submit the vote. In case of errors during the process, custom
exceptions FetchIssueIDError and VoteStoryPointsError are raised and handled accordingly.

Function:
- vote_story_points(request_fn, issue_key, points): Vote story points for a given Jira issue.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the Jira issue to vote story points for.
- points (int): The number of story points to vote for the issue.

Exceptions:
- FetchIssueIDError: Raised when there is an issue fetching the ID of the Jira issue.

Side Effects:
- Makes an HTTP request to fetch the Jira issue ID.
- Prints an error message if there is a failure in fetching the issue ID.

Note:
This function is responsible for voting story points for a specific Jira issue by using the provided request
function to fetch the issue ID.
"""

from exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError


def vote_story_points(request_fn, issue_key, points):
    """
    Vote story points for a given Jira issue.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the Jira issue to vote story points for.
    - points (int): The number of story points to vote for the issue.

    Exceptions:
    - FetchIssueIDError: Raised when there is an issue fetching the ID of the Jira issue.

    Side Effects:
    - Makes an HTTP request to fetch the Jira issue ID.
    - Prints an error message if there is a failure in fetching the issue ID.

    Note:
    This function is responsible for voting story points for a specific Jira issue by using the provided request
    function to fetch the issue ID.
    """

    try:
        issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
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
            json=payload,
        )
        if response.status_code != 200:
            raise VoteStoryPointsError(
                f"JIRA API error ({response.status_code}): {response.text}"
            )
        print(f"✅ Voted {points} story points on issue {issue_key}")
        return
    except (VoteStoryPointsError, VoteStoryPointsError) as e:
        msg = f"❌ Failed to vote on story points: {e}"
        print(msg)
        raise VoteStoryPointsError(e) from e
