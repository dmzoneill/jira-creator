def migrate_issue(request_fn, jira_url, build_payload_fn, old_key, new_type):
    fields = request_fn("GET", f"/rest/api/2/issue/{old_key}")["fields"]
    summary = fields.get("summary", f"Migrated from {old_key}")
    description = fields.get("description", f"Migrated from {old_key}")

    payload = build_payload_fn(summary, description, new_type)
    new_key = request_fn("POST", "/rest/api/2/issue/", json=payload)["key"]

    request_fn(
        "POST",
        f"/rest/api/2/issue/{old_key}/comment",
        json={
            "body": f"Migrated to [{new_key}]({jira_url}/browse/{new_key}) as a {new_type.upper()}."
        },
    )

    transitions = request_fn("GET", f"/rest/api/2/issue/{old_key}/transitions")[
        "transitions"
    ]
    transition_id = next(
        (
            t["id"]
            for t in transitions
            if t["name"].lower() in ["done", "closed", "cancelled"]
        ),
        None,
    )
    if not transition_id and transitions:
        transition_id = transitions[0]["id"]

    if transition_id:
        request_fn(
            "POST",
            f"/rest/api/2/issue/{old_key}/transitions",
            json={"transition": {"id": transition_id}},
        )

    return new_key
