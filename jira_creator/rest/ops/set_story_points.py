from core.env_fetcher import EnvFetcher


def set_story_points(request_fn, issue_key, points):
    field = EnvFetcher.get("JIRA_STORY_POINTS_FIELD")

    payload = {}
    payload["fields"] = {}
    payload["fields"][field] = points

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )
