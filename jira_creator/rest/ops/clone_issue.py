from typing import Callable, Dict

def clone_issue(request_fn: Callable[[str, str, Dict], Dict], issue_key: str) -> Dict:
    path = f"/rest/api/2/issue/{issue_key}/flags"
    return request_fn("POST", path, json_data={})