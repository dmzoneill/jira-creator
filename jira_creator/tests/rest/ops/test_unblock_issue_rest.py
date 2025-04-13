from core.env_fetcher import EnvFetcher


def test_unblock_issue_calls_expected_fields(client):
    called = {}

    def fake_request(method, path, json=None, **kwargs):
        called["method"] = method
        called["path"] = path
        called["json"] = json
        return {}

    client._request = fake_request

    client.unblock_issue("AAP-test_unblock_issue_calls_expected_fields")

    assert called["method"] == "PUT"
    assert (
        called["path"]
        == "/rest/api/2/issue/AAP-test_unblock_issue_calls_expected_fields"
    )
    assert called["json"] == {
        "fields": {
            EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": False},
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
        }
    }
