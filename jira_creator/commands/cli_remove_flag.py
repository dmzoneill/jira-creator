from exceptions.exceptions import RemoveFlagError


def cli_remove_flag(jira, args):
    issue_key = args.issue_key
    try:
        response = jira.remove_flag(issue_key)
        print(f"✅ Removed flag from issue '{issue_key}'")
        return response
    except Exception as e:
        msg = f"❌ Failed to remove flag from issue '{issue_key}': {e}"
        print(msg)
        raise RemoveFlagError(msg)
