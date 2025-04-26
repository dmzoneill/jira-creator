#!/usr/bin/env python
"""
This module provides functionality to construct a payload for creating issues in a Jira system.

The main function, `build_payload`, accepts parameters including summary, description, issue type, project key,
affects version, component name, priority, and epic field. It assembles these parameters into a structured
dictionary that can be used to create an issue in Jira.

Key Features:
- Supports various issue types including epics, with special handling for epic fields.
- Returns a well-defined dictionary that conforms to Jira's API requirements.

Example Usage:
To create a payload for a bug issue:
payload = build_payload("Bug in Login Page", "Fix the issue with the login functionality", "Bug", "PROJ123", "v1.0",
"Authentication", "High", "Epic Name")
"""

# pylint: disable=too-many-arguments too-many-positional-arguments
from typing import Any, Dict


def build_payload(
    summary: str,
    description: str,
    issue_type: str,
    project_key: str,
    affects_version: str,
    component_name: str,
    priority: str,
    epic_field: str,
) -> Dict[str, Any]:
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

    fields: Dict[str, Any] = {
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
