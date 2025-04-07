from core.env_fetcher import EnvFetcher


def set_story_epic(request_fn, issue_key, epic_key):
    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {EnvFetcher.get("JIRA_EPIC_FIELD"): epic_key}},
    )
