from exceptions.exceptions import UnBlockError


def cli_unblock(jira, args):
    try:
        jira.unblock_issue(args.issue_key)
        print(f"✅ {args.issue_key} marked as unblocked")
        return True
    except UnBlockError as e:
        msg = f"❌ Failed to unblock {args.issue_key}: {e}"
        print(msg)
        raise (UnBlockError(msg))
