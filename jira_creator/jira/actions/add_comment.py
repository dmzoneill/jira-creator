def add_comment(request_fn, issue_key, comment):
    path = f"/rest/api/2/issue/{issue_key}/comment"
    payload = {"body": comment}
    request_fn("POST", path, json=payload)
