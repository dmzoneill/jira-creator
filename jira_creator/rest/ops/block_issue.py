from core.env_fetcher import EnvFetcher


def block_issue(request_fn, issue_key, reason):
    blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD")
    reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

    payload = {}
    payload[blocked_field] = {}
    payload[blocked_field]["value"] = True
    payload[reason_field] = reason

    request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json=payload)
