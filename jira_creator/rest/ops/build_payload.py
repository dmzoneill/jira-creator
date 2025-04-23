"""
This module provides a function to build a payload for creating an issue in a Jira system.

The build_payload function takes in various parameters such as summary, description, issue_type, project_key,
affects_version, component_name, priority, and epic_field. It constructs a payload dictionary with these parameters and
returns it.

If the issue type is an epic, it includes an additional field in the payload using the epic_field parameter.

Example:
payload = build_payload("Bug in Login Page", "Fix the issue with the login functionality", "Bug", "PROJ123", "v1.0",
"Authentication", "High", "Epic Name")

Returns:
{
"fields": {
"project": {"key": "PROJ123"},
"summary": "Bug in Login Page",
"description": "Fix the issue with the login functionality",
"issuetype": {"name": "Bug"},
"priority": {"name": "High"},
"versions": [{"name": "v1.0"}],
"components": [{"name": "Authentication"}]
}
}
"""


def build_payload(
    summary,
    description,
    issue_type,
    project_key,
    affects_version,
    component_name,
    priority,
    epic_field,
):
    """
    Builds a payload dictionary for creating an issue in a project.

    Arguments:
    - summary (str): A brief summary or title of the issue.
    - description (str): Detailed description of the issue.
    - issue_type (str): Type of the issue (e.g., Bug, Task, Story).
    - project_key (str): Key of the project where the issue will be created.
    - affects_version (str): Version affected by the issue.
    - component_name (str): Name of the component related to the issue.
    - priority (str): Priority of the issue (e.g., High, Medium, Low).
    - epic_field (str): Field related to the epic the issue belongs to.

    Returns:
    - dict: A dictionary representing the payload for creating an issue with the specified details.

    """
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": issue_type.capitalize()},
        "priority": {"name": priority},
        "versions": [{"name": affects_version}],
        "components": [{"name": component_name}],
    }

    if issue_type.lower() == "epic":
        fields[epic_field] = summary

    return {"fields": fields}
