from exceptions.exceptions import ChangeIssueTypeError


def change_issue_type(request_fn, issue_key, new_type):
    try:
        issue_data = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
        is_subtask = issue_data["fields"]["issuetype"]["subtask"]
        payload = {"fields": {"issuetype": {"name": new_type.capitalize()}}}
        if is_subtask:
            payload["update"] = {"parent": [{"remove": {}}]}

        request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json=payload)
    except ChangeIssueTypeError as e:
        msg = f"❌ Failed to change issue type: {e}"
        print(msg)
        raise (ChangeIssueTypeError(msg))
