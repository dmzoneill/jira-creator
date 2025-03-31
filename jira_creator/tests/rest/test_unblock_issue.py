from unittest.mock import MagicMock

import pytest
from jira.client import JiraClient


@pytest.fixture
def client():
    client = JiraClient()
    client._request = MagicMock(return_value={})
    return client


def test_unblock_issue_calls_expected_fields(client):
    called = {}

    def fake_request(method, path, json=None, **kwargs):
        called["method"] = method
        called["path"] = path
        called["json"] = json
        return {}

    client._request = fake_request

    client.unblock_issue("AAP-123")

    assert called["method"] == "PUT"
    assert called["path"] == "/rest/api/2/issue/AAP-123"
    assert called["json"] == {
        "fields": {
            "customfield_12316543": {"value": "False"},
            "customfield_12316544": "",
        }
    }
