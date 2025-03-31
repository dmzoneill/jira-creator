import re


def search_issues(request_fn, jql):
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

        if not sprints:
            issue["fields"]["sprint"] = "No active sprint"
            continue

        active_sprint = None
        for sprint_str in sprints:
            print(f"Debug: Parsing sprint_str: {sprint_str}")

            name_match = re.search(name_regex, sprint_str)
            sprint_name = name_match.group(1) if name_match else None
            if sprint_name:
                print(f"Debug: Matched sprint name: {sprint_name}")

            state_match = re.search(state_regex, sprint_str)
            sprint_state = state_match.group(1) if state_match else None
            if sprint_state:
                print(f"Debug: Matched sprint state: {sprint_state}")

            if sprint_state == "ACTIVE" and sprint_name:
                active_sprint = sprint_name
                print(f"Debug: Active sprint set to: {active_sprint}")
                break

        issue["fields"]["sprint"] = (
            active_sprint if active_sprint else "No active sprint"
        )

    return issues
