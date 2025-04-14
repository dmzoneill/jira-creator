def cli_add_flag(jira, args):
    issue_key = args.issue_key
    response = jira.add_flag(issue_key)
    return response
