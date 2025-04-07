from unittest.mock import MagicMock

import pytest


def test_status_transition_missing(client):
    # Mock the _request method
    client._request = MagicMock()

    # Simulate an empty list of transitions (no valid transition found)
    client._request.return_value = {"transitions": []}

    # Assert that an exception is raised when trying to set a status
    with pytest.raises(Exception, match="Transition to status 'done' not found"):
        client.set_status("AAP-test_status_transition_missing", "done")
