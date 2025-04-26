#!/usr/bin/env python
"""
This file contains a test case for the 'get_acceptance_criteria' method in the 'client' class.
The test mocks the '_request' method to simulate fetching the acceptance criteria field value from JIRA.
It then calls the 'get_acceptance_criteria' method with a specific test identifier and asserts that the correct
description is returned.

test_get_acceptance_criteria(client):
Retrieve acceptance criteria for a given client.

Arguments:
- client: An object representing the client for which acceptance criteria needs to be retrieved.

This function mocks the _request method of the client object to simulate getting the description, specifically the
acceptance criteria field.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_get_acceptance_criteria(client):
    """
    Retrieve acceptance criteria for a given client.

    Arguments:
    - client: An object representing the client for which acceptance criteria needs to be retrieved.

    This function mocks the _request method of the client object to simulate getting the description, specifically the
    acceptance criteria field.
    """

    # Mock _request method to simulate getting description
    client.request = MagicMock(
        return_value={
            "fields": {EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"): "text"}
        }
    )

    # Call get_description and assert it returns the correct description
    desc = client.get_acceptance_criteria("AAP-test_get_acceptance_criteria")
    assert desc == "text"
