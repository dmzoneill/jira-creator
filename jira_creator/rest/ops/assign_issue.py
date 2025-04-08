from exceptions.exceptions import AssignIssueError


def assign_issue(request_fn, issue_key, assignee):
    try:
        request_fn(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json={"fields": {"assignee": {"name": assignee}}},
        )
        return True
    except AssignIssueError as e:
        msg = f"❌ Failed to assign issue {issue_key}: {e}"
        print(msg)
        raise (AssignIssueError(msg))
