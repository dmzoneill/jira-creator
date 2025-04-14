def cli_set_summary(jira, args):
    issue_key = args.issue_key
    response = jira.add_flag_to_issue(issue_key)
    return response
