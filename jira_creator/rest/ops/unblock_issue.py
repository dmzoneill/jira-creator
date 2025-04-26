from core.env_fetcher import EnvFetcher
from typing import Callable

def unblock_issue(request_fn: Callable[[str, str, dict], None], issue_key: str) -> None:
    blocked_field: str = EnvFetcher.get("JIRA_BLOCKED_FIELD")
    reason_field: str = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

    payload: dict = {
        "fields": {
            blocked_field: {
                "value": False
            },
            reason_field: ""
        }
    }

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )