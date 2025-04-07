import os

from core.env_fetcher import EnvFetcher


def set_story_points(request_fn, issue_key, points):
    field = os.getenv(
        "JIRA_STORY_POINT_FIELD", EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
    )
    payload = {"fields": {field: points}}

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )
