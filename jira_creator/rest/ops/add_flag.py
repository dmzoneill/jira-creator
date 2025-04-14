def add_flag(request_fn, issue_keys) -> dict:
    path = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
    payload = {"issueKeys": [issue_keys], "flag": True}
    return request_fn("POST", path, json=payload)
