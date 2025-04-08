from exceptions.exceptions import RemoveFromSprintError


def remove_from_sprint(request_fn, issue_key):
    try:
        request_fn(
            "POST",
            "/rest/agile/1.0/backlog/issue",
            json={"issues": [issue_key]},
        )
        print(f"✅ Moved {issue_key} to backlog")
    except RemoveFromSprintError as e:
        msg = f"❌ Failed to remove from sprint: {e}"
        print(msg)
        raise (RemoveFromSprintError(msg))
