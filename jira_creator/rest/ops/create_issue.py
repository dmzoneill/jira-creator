def create_issue(request_fn, payload):
    return request_fn("POST", "/rest/api/2/issue/", json=payload).get("key", "")
