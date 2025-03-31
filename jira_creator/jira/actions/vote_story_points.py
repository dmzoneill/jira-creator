def vote_story_points(request_fn, issue_key, points):
    try:
        issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
        issue_id = issue["id"]
    except Exception as e:
        print(f"❌ Failed to fetch issue ID for {issue_key}: {e}")
        return

    payload = {"issueId": issue_id, "vote": points}

    try:
        request_fn(
            "PUT",
            "/rest/eausm/latest/planningPoker/vote",
            json=payload,
        )
        print(f"✅ Voted {points} story points on issue {issue_key}")
    except Exception as e:
        print(f"❌ Failed to vote on story points: {e}")
