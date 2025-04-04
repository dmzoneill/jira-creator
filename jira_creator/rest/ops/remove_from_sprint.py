def remove_from_sprint(request_fn, issue_key):
    try:
        request_fn(
            "POST",
            "/rest/agile/1.0/backlog/issue",
            json={"issues": [issue_key]},
        )
        print(f"✅ Moved {issue_key} to backlog")
    except Exception as e:
        print(f"❌ Failed to remove from sprint: {e}")
