from exceptions.exceptions import BlockError


def cli_block(jira, args):
    try:
        jira.block_issue(args.issue_key, args.reason)
        print(f"✅ {args.issue_key} marked as blocked: {args.reason}")
        return True
    except BlockError as e:
        msg = f"❌ Failed to mark {args.issue_key} as blocked: {e}"
        print(msg)
        raise (BlockError(msg))
