from exceptions.exceptions import ChangeTypeError


def cli_change_type(jira, args):
    try:
        if jira.change_issue_type(args.issue_key, args.new_type):
            print(f"✅ Changed {args.issue_key} to '{args.new_type}'")
            return True
        else:
            print(f"❌ Change failed for {args.issue_key}")
            return False
    except ChangeTypeError as e:
        msg = f"❌ Error: {e}"
        print(msg)
        raise (ChangeTypeError(msg))
