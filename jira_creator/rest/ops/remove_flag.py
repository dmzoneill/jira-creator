def remove_flag(request_fn, issue_key) -> dict:
    path = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
    payload = {"issueKeys": [issue_key]}
    return request_fn("POST", path, json=payload)
