def handle(jira, args):
    try:
        jira.add_to_sprint_by_name(args.issue_key, args.sprint_name)
        print(f"✅ Added to sprint '{args.sprint_name}'")
    except Exception as e:
        print(f"❌ {e}")
