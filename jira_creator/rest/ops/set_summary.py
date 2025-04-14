def set_summary(request_fn, issue_key) -> dict:
    path = "/rest/api/2/issue/AAP-test_set_summary"
    return request_fn("POST", path, json={})
