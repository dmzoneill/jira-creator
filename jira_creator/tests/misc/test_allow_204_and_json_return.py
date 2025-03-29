from jira.client import JiraClient


def test_request_allow_204(monkeypatch):
    client = JiraClient()

    class Response:
        status_code = 204
        text = ""

        def json(self):
            return {}

    monkeypatch.setattr("requests.request", lambda *a, **k: Response())
    result = client._request("GET", "/fake", allow_204=True)
    assert result == {}


def test_request_json_return(monkeypatch):
    client = JiraClient()

    class Response:
        status_code = 200
        text = "ok"

        def json(self):
            return {"ok": True}

    monkeypatch.setattr("requests.request", lambda *a, **k: Response())
    result = client._request("GET", "/fake")
    assert result == {"ok": True}
