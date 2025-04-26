#!/usr/bin/env python
"""
This script defines a unit test for the `migrate_issue` method of a client object, focusing on the migration of issues
without transitions. The test employs mocking to simulate HTTP requests and responses, allowing for controlled testing
of the method's behavior.

Functions:
- test_migrate_no_transitions(client): Tests the migration of issue data for a given client while ignoring
transitions.

Arguments:
- client (Client): An instance of a client that interacts with an issue tracking system.

Side Effects:
- Modifies the test data associated with the specified client, specifically during the issue migration process.

Internal Functions:
- mock_request(method, path, **kwargs): Simulates HTTP requests to a REST API, returning predefined mock responses
based on the requested path.

Return Values of mock_request:
- Returns a dictionary containing mock data that varies according to the request path, which facilitates the testing
of the `migrate_issue` method.
"""

from unittest.mock import MagicMock


def test_migrate_no_transitions(client):
    """
    Migrate the test data without transitions for a given client.

    Arguments:
    - client (Client): An object representing a client for which the test data will be migrated.

    Side Effects:
    - Modifies the test data for the specified client without considering transitions.
    """

    def mock_request(method, path, **kwargs):
        """
        Mock a request to a REST API endpoint.

        Arguments:
        - method (str): The HTTP method used for the request.
        - path (str): The path of the API endpoint being requested.
        - **kwargs: Additional keyword arguments that can be passed but are not used in this function.

        Return:
        - dict: A dictionary containing mock data based on the provided path. The structure of the dictionary varies
        based on the path:
        - If the path starts with "/rest/api/2/issue/AAP-test_migrate_no_transitions/transitions", returns
        {"transitions": []}.
        - If the path starts with "/rest/api/2/issue/AAP-test_migrate_no_transitions", returns {"fields": {"summary":
        "Old", "description": "Old"}}.
        - If the path starts with "/rest/api/2/issue/", returns {"key": "AAP-test_migrate_no_transitions"}.
        """

        if path.startswith(
            "/rest/api/2/issue/AAP-test_migrate_no_transitions/transitions"
        ):
            return {"transitions": []}
        elif path.startswith("/rest/api/2/issue/AAP-test_migrate_no_transitions"):
            return {"fields": {"summary": "Old", "description": "Old"}}
        elif path.startswith("/rest/api/2/issue/"):
            return {"key": "AAP-test_migrate_no_transitions"}

    client.request = MagicMock(side_effect=mock_request)
    client.jira_url = "http://fake"

    new_key = client.migrate_issue("AAP-test_migrate_no_transitions", "story")
    assert new_key == "AAP-test_migrate_no_transitions"
