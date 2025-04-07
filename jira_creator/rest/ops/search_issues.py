import re

from core.env_fetcher import EnvFetcher


def search_issues(request_fn, jql):
    params = {
        "jql": jql,
        "fields": (
            "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
        ),
        "maxResults": 200,
    }

    issues = request_fn("GET", "/rest/api/2/search", params=params).get("issues", [])

    name_regex = r"name\s*=\s*([^,]+)"
    state_regex = r"state\s*=\s*([A-Za-z]+)"

    for issue in issues:
        sprints = issue.get("fields", {}).get(EnvFetcher.get("JIRA_SPRINT_FIELD"), [])

        if not sprints:
            issue["fields"]["sprint"] = "No active sprint"
            continue

        active_sprint = None
        for sprint_str in sprints:
            name_match = re.search(name_regex, sprint_str)
            sprint_name = name_match.group(1) if name_match else None

            state_match = re.search(state_regex, sprint_str)
            sprint_state = state_match.group(1) if state_match else None

            if sprint_state == "ACTIVE" and sprint_name:
                active_sprint = sprint_name
                break

        issue["fields"]["sprint"] = (
            active_sprint if active_sprint else "No active sprint"
        )

    return issues
