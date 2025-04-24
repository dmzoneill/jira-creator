#!/usr/bin/env python
"""
Set up a mock for the get_current_user method in the provided client object to always return the string "me".
"""
from unittest.mock import MagicMock


def test_list_issues_defaults(client):
    """
    Set up a mock for the get_current_user method in the provided client object to always return the string "me".
    """

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="me")

    # Mock _request to return an empty issue list
    client.request = MagicMock(return_value={"issues": []})

    # Call list_issues and assert it returns an empty list
    result = client.list_issues()
    assert result == []
