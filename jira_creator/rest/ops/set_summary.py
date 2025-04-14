def set_summary(request_fn, issue_key) -> dict:
    path = f"/rest/api/2/issue/AAP-test_set_summary"
    return request_fn("POST", path, json={})
