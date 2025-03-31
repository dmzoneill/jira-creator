def unassign_issue(request_fn, issue_key):
    try:
        request_fn(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json={"fields": {"assignee": None}},
            allow_204=True,
        )
        return True
    except Exception as e:
        print(f"❌ Failed to unassign issue {issue_key}: {e}")
        return False
