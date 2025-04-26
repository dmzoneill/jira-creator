from typing import Callable, Dict, Any

def view_issue(request_fn: Callable[[str, str], Dict[str, Any]], issue_key: str) -> Dict[str, Any]:
    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"]