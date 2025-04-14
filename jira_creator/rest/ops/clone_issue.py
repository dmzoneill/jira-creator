def clone_issue(request_fn, issue_key) -> dict:
    path = f"/rest/api/2/issue/{issue_key}/flags"
    # payload = {"flag": flag_name}
    return request_fn("POST", path, json={})
