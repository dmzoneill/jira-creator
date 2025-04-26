from typing import Callable

def get_issue_type(request_fn: Callable[[str, str], dict], issue_key: str) -> str:
    issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
    return issue["fields"]["issuetype"]["name"]