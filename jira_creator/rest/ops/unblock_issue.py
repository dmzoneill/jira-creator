import os


def unblock_issue(request_fn, issue_key):
    blocked_field = os.getenv("JIRA_BLOCKED_FIELD", "customfield_12316543")
    reason_field = os.getenv("JIRA_BLOCKED_REASON_FIELD", "customfield_12316544")

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
