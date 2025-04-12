from exceptions.exceptions import ViewIssueError


def cli_view_issue(jira, args):
    try:
        issue = jira.view_issue(args.issue_key)

        # Create a new dictionary with real names as keys
        updated_issue = {}

        for key in issue:
            # Check if the key is a custom field
            if "customfield" in key:
                real_name = jira.get_field_name(key)
                updated_issue[real_name] = issue[key]
            else:
                # For non-custom fields, keep the original key
                updated_issue[key] = issue[key]

        # Sort the dictionary by the real names (keys)
        for key in sorted(updated_issue.keys()):
            print(f"{key} : {updated_issue[key]}")

        return issue
    except ViewIssueError as e:
        msg = f"❌ Unable to view issue: {e}"
        print(msg)
        raise (ViewIssueError(msg))
