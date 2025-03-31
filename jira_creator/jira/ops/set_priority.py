def set_priority(request_fn, issue_key, priority):
    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {"priority": {"name": priority}}},
    )
