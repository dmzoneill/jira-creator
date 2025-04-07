import os

from core.env_fetcher import EnvFetcher


def unblock_issue(request_fn, issue_key):
    blocked_field = os.getenv(
        "JIRA_BLOCKED_FIELD", EnvFetcher.get("JIRA_BLOCKED_FIELD")
    )
    reason_field = os.getenv(
        "JIRA_BLOCKED_REASON_FIELD", EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")
    )

    payload = {
        "fields": {
            blocked_field: {"value": "False"},
            reason_field: "",  # Clear reason
        }
    }

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )
