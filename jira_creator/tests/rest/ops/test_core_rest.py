#!/usr/bin/env python
"""
This script defines a function test_build_payload_with_patch_dict that tests the build_payload method of a client
object. The function sets up summary, description, and issue_type variables, builds a payload using the client's
build_payload method, and then asserts various fields of the payload dictionary. The commented-out
test_missing_env_raises function is not currently in use.

test_build_payload_with_patch_dict(client):
Builds a payload dictionary for creating an issue with a patch request.

Arguments:
- client (object): An object representing the client connection.

Return:
This function does not return anything.

Side Effects:
Modifies the payload dictionary with the provided summary, description, and issue type.
"""


def test_build_payload_with_patch_dict(client):
    """
    Builds a payload dictionary for creating an issue with a patch request.

    Arguments:
    - client (object): An object representing the client connection.

    Side Effects:
    Modifies the payload dictionary with the provided summary, description, and issue type.
    """

    summary = "Fix login issue"
    description = "Steps to reproduce..."
    issue_type = "bug"

    payload = client.build_payload(summary, description, issue_type)
    fields = payload["fields"]

    assert fields["project"]["key"] == "XYZ"
    assert fields["summary"] == summary
    assert fields["description"] == description
    assert fields["issuetype"]["name"] == "Bug"
    assert fields["priority"]["name"] == "High"
    assert fields["versions"][0]["name"] == "v1.2.3"
    assert fields["components"][0]["name"] == "backend"


# def test_missing_env_raises(client):
#     with pytest.raises(MissingConfigVariable):
#         JiraClient()
