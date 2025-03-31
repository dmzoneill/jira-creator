import os


def set_story_points(request_fn, issue_key, points):
    field = os.getenv("JIRA_STORY_POINT_FIELD", "customfield_12310243")
    payload = {"fields": {field: points}}

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )
