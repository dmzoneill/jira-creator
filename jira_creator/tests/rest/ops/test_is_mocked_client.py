from unittest.mock import MagicMock, patch

import pytest
from rest.client import JiraClient


# Test for ensure_requests_is_mocked when requests is not mocked
def test_ensure_requests_is_mocked_not_mocked():
    client = JiraClient()

    # Patch is_running_under_pytest to return True, simulating pytest environment
    with patch.object(client, "is_running_under_pytest", return_value=True):
        # Ensure an exception is raised when requests.request is not mocked
        with pytest.raises(
            Exception, match="Running under pytest but requests is not mocked"
        ):
            client.ensure_requests_is_mocked()


# Test for ensure_requests_is_mocked when requests is mocked


def test_ensure_requests_is_mocked_mocked():
    client = JiraClient()

    # Mock requests.request using MagicMock
    with patch("requests.request", MagicMock()):
        # Patch is_running_under_pytest to return True, simulating pytest environment
        with patch.object(client, "is_running_under_pytest", return_value=True):
            # Ensure no exception is raised when requests.request is mocked
            client.ensure_requests_is_mocked()
