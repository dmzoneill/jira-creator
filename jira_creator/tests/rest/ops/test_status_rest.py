def test_set_status(client):
    # Simulating the side effects for multiple calls
    client._request.side_effect = [{"transitions": [{"name": "Done", "id": "2"}]}, {}]

    client.set_status("AAP-test_set_status", "Done")

    # Assert that the request was called twice
    assert client._request.call_count == 2
