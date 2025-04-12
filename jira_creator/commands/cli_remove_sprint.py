from exceptions.exceptions import RemoveFromSprintError


def cli_remove_sprint(jira, args):
    try:
        jira.remove_from_sprint(args.issue_key)
        print("✅ Removed from sprint")
        return True
    except RemoveFromSprintError as e:
        msg = f"❌ Failed to remove sprint: {e}"
        print(msg)
        raise (RemoveFromSprintError(msg))
