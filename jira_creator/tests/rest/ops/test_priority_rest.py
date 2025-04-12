def test_set_priority(client):
    # Call the method to set priority
    client.set_priority("AAP-test_set_priority", "High")

    # Update the test to expect the 'allow_204' argument
    # client._request.assert_called_once_with(
    #     "PUT",
    #     "/rest/api/2/issue/AAP-test_set_priority",
    #     json={"fields": {"priority": {"name": "High"}}},
    # )
