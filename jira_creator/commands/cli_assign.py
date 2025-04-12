def cli_assign(jira, args):
    success = jira.assign_issue(args.issue_key, args.assignee)
    print(
        f"✅ assigned {args.issue_key} to {args.assignee}"
        if success
        else f"❌ Could not assign {args.issue_key} to {args.assignee}"
    )
    return True if success else False
