def set_sprint(request_fn, issue_key, sprint_id):
    payload = {
        "fields": {"customfield_12310940": None if not sprint_id else [str(sprint_id)]}
    }

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )
