from exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError


def vote_story_points(request_fn, issue_key, points):
    try:
        issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
        issue_id = issue["id"]
    except FetchIssueIDError as e:
        msg = f"❌ Failed to fetch issue ID for {issue_key}: {e}"
        print(msg)
        raise (FetchIssueIDError(msg))

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
        raise (VoteStoryPointsError(msg))
