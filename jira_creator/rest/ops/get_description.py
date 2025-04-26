def get_description(request_fn: callable, issue_key: str) -> str:
    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"].get(
        "description", ""
    )