import os

from core.env_fetcher import EnvFetcher


def block_issue(request_fn, issue_key, reason):
    blocked_field = os.getenv(
        "JIRA_BLOCKED_FIELD", EnvFetcher.get("JIRA_BLOCKED_FIELD")
    )
    reason_field = os.getenv(
        "JIRA_BLOCKED_REASON_FIELD", EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")
    )

    payload = {
        "fields": {
            blocked_field: {"value": "True"},
            reason_field: reason,
        }
    }

    request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json=payload)
