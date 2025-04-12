from exceptions.exceptions import MigrateError


def cli_migrate(jira, args):
    try:
        new_key = jira.migrate_issue(args.issue_key, args.new_type)
        print(
            f"✅ Migrated {args.issue_key} to {new_key}: {jira.jira_url}/browse/{new_key}"
        )
        return new_key
    except MigrateError as e:
        msg = f"❌ Migration failed: {e}"
        print(msg)
        raise (MigrateError(msg))
