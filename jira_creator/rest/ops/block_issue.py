import os


def block_issue(request_fn, issue_key, reason):
    blocked_field = os.getenv("JIRA_BLOCKED_FIELD", "customfield_12316543")
    reason_field = os.getenv("JIRA_BLOCKED_REASON_FIELD", "customfield_12316544")

    payload = {
        "fields": {
            blocked_field: {"value": "True"},
            reason_field: reason,
        }
    }

    request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json=payload)
