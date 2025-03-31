def add_to_sprint_by_name(request_fn, board_id, issue_key, sprint_name):
    if not board_id:
        raise Exception("❌ JIRA_BOARD_ID not set in environment")

    sprints = request_fn("GET", f"/rest/agile/1.0/board/{board_id}/sprint").get(
        "values", []
    )
    sprint_id = next((s["id"] for s in sprints if s["name"] == sprint_name), None)

    if not sprint_id:
        raise Exception(f"❌ Could not find sprint named '{sprint_name}'")

    request_fn(
        "POST",
        f"/rest/agile/1.0/sprint/{sprint_id}/issue",
        json={"issues": [issue_key]},
    )
    print(f"✅ Added {issue_key} to sprint '{sprint_name}' on board {board_id}")
