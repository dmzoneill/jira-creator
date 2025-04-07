def test_build_payload_epic(client):
    # Mock values for the test
    client.epic_field = "nonsense"  # Example epic field
    client.project_key = "PROJ"
    client.priority = "High"
    client.affects_version = "1.0"
    client.component_name = "Component1"

    # Call build_payload with "epic" as issue_type
    result = client.build_payload(
        summary="Epic Summary", description="Epic Description", issue_type="epic"
    )

    # Check if the epic field is present in the fields
    assert client.epic_field in result["fields"]
    assert result["fields"][client.epic_field] == "Epic Summary"


def test_build_payload_non_epic(client):
    # Mock values for the test
    client.epic_field = "nonsense"  # Example epic field
    client.project_key = "PROJ"
    client.priority = "High"
    client.affects_version = "1.0"
    client.component_name = "Component1"

    # Call build_payload with a non-"epic" issue_type
    result = client.build_payload(
        summary="Story Summary", description="Story Description", issue_type="story"
    )

    # Check if the epic field is not present in the fields
    assert client.epic_field not in result["fields"]
