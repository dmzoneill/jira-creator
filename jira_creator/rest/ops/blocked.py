from core.env_fetcher import EnvFetcher


# /* jscpd:ignore-start */
def blocked(list_issues_fn, project=None, component=None, assignee=None):
    issues = list_issues_fn(project=project, component=component, assignee=assignee)

    blocked_issues = []
    for issue in issues:
        fields = issue["fields"]
        is_blocked = (
            fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value") == "True"
        )
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
                    "reason": fields.get(
                        EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"), "(no reason)"
                    ),
                    "summary": fields["summary"],
                }
            )
    return blocked_issues


# /* jscpd:ignore-end */
