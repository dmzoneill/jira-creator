def handle(jira, args):
    try:
        jira.block_issue(args.issue_key, args.reason)
        print(f"✅ {args.issue_key} marked as blocked: {args.reason}")
    except Exception as e:
        print(f"❌ Failed to mark {args.issue_key} as blocked: {e}")
