from exceptions.exceptions import UnassignIssueError


def unassign_issue(request_fn, issue_key):
    try:
        request_fn(
            "PUT", f"/rest/api/2/issue/{issue_key}", json={"fields": {"assignee": None}}
        )
        return True
    except UnassignIssueError as e:
        msg = f"❌ Failed to unassign issue {issue_key}: {e}"
        print(msg)
        raise (UnassignIssueError(msg))
