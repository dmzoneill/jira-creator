import re


def list_issues(
    request_fn,
    get_current_user_fn,
    project_key,
    component_name,
    project=None,
    component=None,
    assignee=None,
    status=None,
    summary=None,
    show_reason=False,
    blocked=False,
    unblocked=False,
):
    jql_parts = []
    if project := project or project_key:
        jql_parts.append(f'project="{project}"')
    if component := component or component_name:
        jql_parts.append(f'component="{component}"')
    if username := assignee or get_current_user_fn():
        jql_parts.append(f'assignee="{username}"')

    if status:
        jql_parts.append(f'status="{status}"')
    if summary:
        jql_parts.append(f'summary~"{summary}"')
    if blocked:
        jql_parts.append('customfield_12316543="True"')
    if unblocked:
        jql_parts.append('customfield_12316543!="True"')

    jql = " AND ".join(jql_parts) + ' AND status NOT IN ("Closed", "Done", "Cancelled")'

    params = {
        "jql": jql,
        "fields": (
            "summary,status,assignee,priority,"
            "customfield_12310243,customfield_12310940,customfield_12316543"
        ),
        "maxResults": 200,
    }
    issues = request_fn("GET", "/rest/api/2/search", params=params).get("issues", [])

    name_regex = r"name\s*=\s*([^,]+)"
    state_regex = r"state\s*=\s*([A-Za-z]+)"

    for issue in issues:
        sprints = issue.get("fields", {}).get("customfield_12310940", [])
        if sprints is None:
            sprints = []

        active_sprint = None
        for sprint_str in sprints:
            name_match = re.search(name_regex, sprint_str)
            sprint_name = name_match.group(1) if name_match else None

            state_match = re.search(state_regex, sprint_str)
            sprint_state = state_match.group(1) if state_match else None

            if sprint_state == "ACTIVE" and sprint_name:
                active_sprint = sprint_name
                break

        issue["sprint"] = active_sprint if active_sprint else "No active sprint"

    return issues
