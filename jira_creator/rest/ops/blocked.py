"""
This module includes a function called blocked that retrieves a list of issues based on certain criteria and filters
out the blocked issues.
The function takes a list_issues_fn function as input along with optional project, component, and assignee parameters.
It checks each issue for a specific field value (JIRA_BLOCKED_FIELD) to determine if it is blocked.
If an issue is blocked, it constructs a dictionary containing key information about the issue like key, status,
assignee, reason, and summary.
The function returns a list of dictionaries representing the blocked issues.
"""
from core.env_fetcher import EnvFetcher


# /* jscpd:ignore-start */
def blocked(list_issues_fn, project=None, component=None, assignee=None):
    """
    Retrieve a list of issues based on specified project, component, and assignee.
    
    Arguments:
    - list_issues_fn (function): A function that returns a list of issues based on project, component, and assignee
    parameters.
    - project (str): The project name to filter the issues. Defaults to None.
    - component (str): The component name to filter the issues. Defaults to None.
    - assignee (str): The assignee name to filter the issues. Defaults to None.
    
    No return value.
    
    Side Effects:
    - Modifies the 'issues' list by populating it with the filtered list of issues.
    """

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
