def blocked(list_issues_fn, project=None, component=None, user=None):
    issues = list_issues_fn(project=project, component=component, assignee=user)

    blocked_issues = []
    for issue in issues:
        fields = issue["fields"]
        is_blocked = fields.get("customfield_12316543", {}).get("value") == "True"
        if is_blocked:
            blocked_issues.append(
                {
                    "key": issue["key"],
                    "status": fields["status"]["name"],
                    "assignee": (
                        fields["assignee"]["displayName"]
                        if fields["assignee"]
                        else "Unassigned"
                    ),
                    "reason": fields.get("customfield_12316544", "(no reason)"),
                    "summary": fields["summary"],
                }
            )
    return blocked_issues
