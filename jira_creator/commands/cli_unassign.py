def cli_unassign(jira, args):
    success = jira.unassign_issue(args.issue_key)
    print(
        f"✅ Unassigned {args.issue_key}"
        if success
        else f"❌ Could not unassign {args.issue_key}"
    )
    return True if success else False
