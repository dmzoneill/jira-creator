from typing import Callable, Dict

def create_issue(request_fn: Callable[[str, str, Dict], Dict], payload: Dict) -> str:
    return request_fn("POST", "/rest/api/2/issue/", json_data=payload).get("key", "")