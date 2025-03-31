def handle(fields, ai_provider):
    problems = []

    issue_type = fields.get("issuetype", {}).get("name")
    status = fields.get("status", {}).get("name")

    summary = fields.get("summary", "")
    description = fields.get("description", "")
    epic_link = fields.get("customfield_10008")  # Epic Link
    sprint_field = fields.get("customfield_12310940")  # Sprint field
    priority = fields.get("priority")
    story_points = fields.get("customfield_12310243")
    blocked_value = fields.get("customfield_12316543", {}).get("value")
    blocked_reason = fields.get("customfield_12316544")

    # ✅ Check: In Progress must be assigned to someone
    if status == "In Progress" and not fields.get("assignee"):
        problems.append("❌ Issue is In Progress but unassigned")

    # ✅ Check: Story must be assigned to an Epic
    if issue_type == "Story" and not epic_link:
        problems.append("❌ Story has no assigned Epic")

    # ✅ Check: In Progress must have a Sprint
    if status == "In Progress" and not sprint_field:
        problems.append("❌ Issue is In Progress but not assigned to a Sprint")

    # ✅ Check: Priority set
    if not priority:
        problems.append("❌ Priority not set")

    # ✅ Check: Story points
    if story_points is None:
        problems.append("❌ Story points not assigned")

    # ✅ Check: Blocked issues must have a reason
    if blocked_value == "True" and not blocked_reason:
        problems.append("❌ Issue is blocked but has no blocked reason")

    # ✅ AI-based content quality check
    if summary and description:
        # Validate Summary
        default_summary_prompt = (
            "Check the quality of the following Jira summary. "
            "Is it clear, concise, and informative? Respond with 'OK' if fine or explain why not."
        )
        reviewed_summary = ai_provider.improve_text(default_summary_prompt, summary)
        if "ok" not in reviewed_summary.lower():
            problems.append(f"❌ Summary: {reviewed_summary.strip()}")

        # Validate Description
        default_description_prompt = (
            "Check the quality of the following Jira description. "
            "Is it well-structured, informative, and helpful? Respond with 'OK' if fine or explain why not."
        )
        reviewed_description = ai_provider.improve_text(
            default_description_prompt, description
        )
        if "ok" not in reviewed_description.lower():
            problems.append(f"❌ Description: {reviewed_description.strip()}")

    return problems
