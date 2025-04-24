#!/usr/bin/env python
"""
This script defines a test function 'test_migrate_no_transitions' that tests the 'migrate_issue' method of a client
object. It mocks the HTTP requests made by the client using 'MagicMock' from 'unittest.mock'. The mock_request function
simulates different responses based on the requested path. The test verifies that the 'migrate_issue' method returns
the expected new issue key.

Functions:
- test_migrate_no_transitions(client): Migrate the test data without transitions for a given client.

Arguments:
- client (Client): An object representing a client for which the test data will be migrated.

Side Effects:
- Modifies the test data for the specified client without considering transitions.

Internal Functions:
- mock_request(method, path, **kwargs): Mock a request to a REST API endpoint.

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
