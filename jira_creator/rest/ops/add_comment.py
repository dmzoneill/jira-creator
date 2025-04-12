def add_comment(request_fn, issue_key, comment) -> dict:
    path = f"/rest/api/2/issue/{issue_key}/comment"
    payload = {"body": comment}
    return request_fn("POST", path, json=payload)
