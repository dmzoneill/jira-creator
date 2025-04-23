"""
This module contains a function to search for JIRA issues based on a JQL query.

The 'search_issues' function takes two parameters: 'request_fn' for making HTTP requests and 'jql' for the JIRA Query
Language query.
It constructs the necessary parameters for the JIRA API request, including specific fields to retrieve.
The function then retrieves a list of issues matching the JQL query and processes each issue to extract sprint
information.
If an issue is associated with an active sprint, it updates the issue with the active sprint name; otherwise, it sets
the sprint as 'No active sprint'.
The function returns a list of processed issues.

Note: This function relies on the 'EnvFetcher' class from 'core.env_fetcher' for fetching environment variables related
to JIRA fields.
"""
import re

from core.env_fetcher import EnvFetcher


def search_issues(request_fn, jql):
    """
    Search for issues in JIRA based on the provided JQL query.
    
    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - jql (str): JIRA Query Language (JQL) query to filter the search results.
    
    Return:
    None
    """

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
