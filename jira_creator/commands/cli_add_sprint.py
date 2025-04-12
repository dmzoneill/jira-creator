from exceptions.exceptions import AddSprintError


def cli_add_sprint(jira, args):
    try:
        jira.add_to_sprint_by_name(args.issue_key, args.sprint_name)
        print(f"✅ Added to sprint '{args.sprint_name}'")
        return True
    except AddSprintError as e:
        msg = f"❌ {e}"
        print(msg)
        raise (AddSprintError(msg))
