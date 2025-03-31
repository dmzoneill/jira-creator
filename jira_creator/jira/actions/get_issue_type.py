def get_issue_type(request_fn, issue_key):
    issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
    return issue["fields"]["issuetype"]["name"]
