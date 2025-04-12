from exceptions.exceptions import SetStatusError


def cli_set_status(jira, args):
    try:
        jira.set_status(args.issue_key, args.status)
        print(f"✅ Status set to '{args.status}'")
        return True
    except SetStatusError as e:
        msg = f"❌ Failed to update status: {e}"
        print(msg)
        raise (SetStatusError(msg))
