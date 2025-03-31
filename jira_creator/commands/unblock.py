def handle(jira, args):
    try:
        jira.unblock_issue(args.issue_key)
        print(f"✅ {args.issue_key} marked as unblocked")
    except Exception as e:
        print(f"❌ Failed to unblock {args.issue_key}: {e}")
