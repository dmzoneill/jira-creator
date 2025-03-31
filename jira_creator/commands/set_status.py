def handle(jira, args):
    try:
        jira.set_status(args.issue_key, args.status)
        print(f"✅ Status set to '{args.status}'")
    except Exception as e:
        print(f"❌ Failed to update status: {e}")
