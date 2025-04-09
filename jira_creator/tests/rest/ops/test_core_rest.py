def test_build_payload_with_patch_dict(client):
    summary = "Fix login issue"
    description = "Steps to reproduce..."
    issue_type = "bug"

    payload = client.build_payload(summary, description, issue_type)
    fields = payload["fields"]

    assert fields["project"]["key"] == "XYZ"
    assert fields["summary"] == summary
    assert fields["description"] == description
    assert fields["issuetype"]["name"] == "Bug"
    assert fields["priority"]["name"] == "High"
    assert fields["versions"][0]["name"] == "v1.2.3"
    assert fields["components"][0]["name"] == "backend"


# def test_missing_env_raises(client):
#     with pytest.raises(MissingConfigVariable):
#         JiraClient()
