def handle(jira, args):
    try:
        jira.set_priority(args.issue_key, args.priority)
        print(f"✅ Priority set to '{args.priority}'")
    except Exception as e:
        print(f"❌ Failed to set priority: {e}")
