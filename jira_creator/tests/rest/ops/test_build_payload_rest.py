#!/usr/bin/env python
"""
This file contains test functions for the build_payload method of a client class.
The test_build_payload_epic function tests the build_payload method with "epic" as the issue type,
while the test_build_payload_non_epic function tests it with a non-"epic" issue type.
Mock values are set for client attributes such as epic_field, project_key, priority, affects_version, and
component_name.
Assertions are used to verify the presence or absence of the epic field in the result fields based on the issue type
provided.

test_build_payload_epic(client):
- Builds a payload for an epic in a project.
- Arguments:
- client (Client): An object representing the client connection.
- Side Effects:
- Modifies client attributes: epic_field, project_key, priority, affects_version, component_name.

test_build_payload_non_epic(client):
- Builds a payload using client attributes for a non-epic issue.
- Arguments:
- client (Client): An object containing attributes related to the client.
- Side Effects:
- Modifies the client object by setting values for epic_field, project_key, priority, affects_version, and
component_name.
"""


def test_build_payload_epic(client):
    """
    Builds a payload for an epic in a project.

    Arguments:
    - client (Client): An object representing the client connection.

    Side Effects:
    - Modifies client attributes: epic_field, project_key, priority, affects_version, component_name.
    """

    # Mock values for the test
    client.epic_field = "nonsense"  # Example epic field
    client.project_key = "PROJ"
    client.priority = "High"
    client.affects_version = "1.0"
    client.component_name = "Component1"

    # Call build_payload with "epic" as issue_type
    result = client.build_payload(
        summary="Epic Summary", description="Epic Description", issue_type="epic"
    )

    # Check if the epic field is present in the fields
    assert client.epic_field in result["fields"]
    assert result["fields"][client.epic_field] == "Epic Summary"


def test_build_payload_non_epic(client):
    """
    Builds a payload using client attributes for a non-epic issue.

    Arguments:
    - client (Client): An object containing attributes related to the client.

    Side Effects:
    - Modifies the client object by setting values for epic_field, project_key, priority, affects_version, and
    component_name.
    """

    # Mock values for the test
    client.epic_field = "nonsense"  # Example epic field
    client.project_key = "PROJ"
    client.priority = "High"
    client.affects_version = "1.0"
    client.component_name = "Component1"

    # Call build_payload with a non-"epic" issue_type
    result = client.build_payload(
        summary="Story Summary", description="Story Description", issue_type="story"
    )

    # Check if the epic field is not present in the fields
    assert client.epic_field not in result["fields"]
