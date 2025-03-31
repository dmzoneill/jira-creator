def handle(jira, args):
    try:
        jira.remove_from_sprint(args.issue_key)
        print("✅ Removed from sprint")
    except Exception as e:
        print(f"❌ Failed to remove sprint: {e}")
