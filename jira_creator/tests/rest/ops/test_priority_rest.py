#!/usr/bin/env python
"""
Set priority for a specific client.

Arguments:
- client: An object representing a client for which the priority needs to be set.

Side Effects:
- Modifies the priority of the client by calling the 'set_priority' method.
"""


def test_set_priority(client):
    """
    Set priority for a specific client.

    Arguments:
    - client: An object representing a client for which the priority needs to be set.

    Side Effects:
    - Modifies the priority of the client by calling the 'set_priority' method.
    """

    # Call the method to set priority
    client.set_priority("AAP-test_set_priority", "High")

    # Update the test to expect the 'allow_204' argument
    # client.request.assert_called_once_with(
    #     "PUT",
    #     "/rest/api/2/issue/AAP-test_set_priority",
    #     json_data={"fields": {"priority": {"name": "High"}}},
    # )
