def handle(jira, args):
    try:
        new_key = jira.migrate_issue(args.issue_key, args.new_type)
        print(
            f"✅ Migrated {args.issue_key} to {new_key}: {jira.jira_url}/browse/{new_key}"
        )
    except Exception as e:
        print(f"❌ Migration failed: {e}")
