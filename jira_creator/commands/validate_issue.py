def handle(fields):
    problems = []

    if not fields.get("summary"):
        problems.append("❌ Missing summary")
    if not fields.get("description"):
        problems.append("❌ Missing description")
    if not fields.get("priority"):
        problems.append("❌ Priority not set")

    issue_type = fields.get("issuetype", {}).get("name")
    if issue_type not in ["Bug", "Epic"] and fields.get("status", {}).get(
        "name"
    ) not in ["New", "Refinement"]:
        if fields.get("customfield_12310243") in [None, ""]:
            problems.append("❌ Story points not assigned")

    if fields.get("customfield_12316543", {}).get("value") == "True":
        reason = fields.get("customfield_12316544")
        if not reason:
            problems.append("❌ Issue is blocked but has no blocked reason")

    if fields.get("status", {}).get("name") == "In Progress" and not fields.get(
        "assignee"
    ):
        problems.append("❌ Issue is In Progress but unassigned")

    return problems
