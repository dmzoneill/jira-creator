def test_rest_view_issue(client):
    # Call the method to set priority
    client.view_issue("AAP-test_rest_view_issue")

    # Update the test to expect the 'allow_204' argument
    client._request.assert_called_once_with(
        "GET",
        "/rest/api/2/issue/AAP-test_rest_view_issue",
    )
