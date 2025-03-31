def handle(jira, args):
    try:
        issues = jira.list_issues(
            project=args.project,
            component=args.component,
            user=args.user or jira.get_current_user(),
        )

        if not issues:
            print("✅ No issues found.")
            return

        blocked_issues = []
        for issue in issues:
            fields = issue["fields"]
            is_blocked = fields.get("customfield_12316543", {}).get("value") == "True"
            if is_blocked:
                blocked_issues.append(
                    {
                        "key": issue["key"],
                        "status": fields["status"]["name"],
                        "assignee": (
                            fields["assignee"]["displayName"]
                            if fields["assignee"]
                            else "Unassigned"
                        ),
                        "reason": fields.get("customfield_12316544", "(no reason)"),
                        "summary": fields["summary"],
                    }
                )

        if not blocked_issues:
            print("✅ No blocked issues found.")
            return

        print("🔒 Blocked issues:")
        print("-" * 80)
        for i in blocked_issues:
            print(f"{i['key']} [{i['status']}] — {i['assignee']}")
            print(f"  🔸 Reason: {i['reason']}")
            print(f"  📄 {i['summary']}")
            print("-" * 80)

    except Exception as e:
        print(f"❌ Failed to list blocked issues: {e}")
