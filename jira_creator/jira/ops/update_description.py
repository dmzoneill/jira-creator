def update_description(request_fn, issue_key, new_description):
    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {"description": new_description}},
    )
