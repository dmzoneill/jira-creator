from core.env_fetcher import EnvFetcher


def unblock_issue(request_fn, issue_key):
    blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD")
    reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

    payload = {}
    payload["fields"] = {}
    payload["fields"][blocked_field] = {}
    payload["fields"][blocked_field]["value"] = False
    payload["fields"][reason_field] = ""

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )
