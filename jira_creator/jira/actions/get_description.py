def get_description(request_fn, issue_key):
    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"].get(
        "description", ""
    )
