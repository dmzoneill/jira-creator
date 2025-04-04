def handle(jira, args):
    try:
        jira.set_story_epic(args.issue_key, args.epic_key)
        print(f"✅ Story's epic set to '{args.epic_key}'")
    except Exception as e:
        print(f"❌ Failed to set epic: {e}")
