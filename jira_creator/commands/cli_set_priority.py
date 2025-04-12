from exceptions.exceptions import SetPriorityError


def cli_set_priority(jira, args):
    try:
        jira.set_priority(args.issue_key, args.priority)
        print(f"✅ Priority set to '{args.priority}'")
        return True
    except SetPriorityError as e:
        msg = f"❌ Failed to set priority: {e}"
        print(msg)
        raise (SetPriorityError(msg))
