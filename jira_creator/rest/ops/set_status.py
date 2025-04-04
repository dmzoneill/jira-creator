def set_status(request_fn, issue_key, target_status):
    transitions = request_fn("GET", f"/rest/api/2/issue/{issue_key}/transitions").get(
        "transitions", []
    )

    transition_id = next(
        (t["id"] for t in transitions if t["name"].lower() == target_status.lower()),
        None,
    )

    if not transition_id:
        print("Valid Transitions:")
        for t in transitions:
            print(t["name"])
        raise Exception(f"❌ Transition to status '{target_status}' not found")

    request_fn(
        "POST",
        f"/rest/api/2/issue/{issue_key}/transitions",
        json={"transition": {"id": transition_id}},
    )
    print(f"✅ Changed status of {issue_key} to '{target_status}'")
