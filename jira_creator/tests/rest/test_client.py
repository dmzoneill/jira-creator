#!/usr/bin/env python
"""
Unit tests for the JiraClient class in the rest.client module.

This module contains unit tests that validate the functionality of the JiraClient's request method,
covering various scenarios including:

- Successful requests with valid JSON responses.
- Handling of empty responses and different types of HTTP errors (404, 401, 500).
- Exception handling for network failures and invalid JSON responses.
- Retry logic for transient server errors.
- Generation of curl commands for different request configurations.

The tests utilize the pytest framework along with mocking to simulate HTTP requests and responses,
ensuring that no actual network calls are made during testing.
"""

from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import JiraClientRequestError
from requests.exceptions import RequestException
from rest.client import JiraClient


# Test Case 1: Valid JSON response
@patch("rest.client.time.sleep")
@patch("rest.client.requests.request")  # Mock the request to simulate an API response
def test_request_success_valid_json(mock_request, mock_sleep):
    """
    This function is a test function that simulates a successful request to a Jira client with valid JSON response. It
    takes two mock objects as parameters: mock_request and mock_sleep. It initializes a JiraClient object for testing
    purposes.
    """

    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"key": "value"}'
    mock_response.json.return_value = {"key": "value"}

    mock_request.return_value = mock_response

    result = client.request("GET", "/rest/api/2/issue/ISSUE-123")
    assert result == {"key": "value"}
    mock_request.assert_called_once()


# Test Case: Empty response content (tests the line `if not response.content.strip():`)
@patch("rest.client.time.sleep")  # Mock time.sleep to prevent delays in retry logic
@patch("rest.client.requests.request")  # Mock the request to simulate an empty response
def test_request_empty_response_content(mock_request, mock_sleep):
    """
    This function initializes a JiraClient object for making requests to a Jira server. It relies on external
    dependencies `mock_request` and `mock_sleep` for testing purposes.

    No arguments are directly passed to the function. It simulates an empty response (no content in the body) from the
    Jira server using mock objects.

    The function makes a request to the Jira server with the specified method and endpoint
    ("/rest/api/2/issue/ISSUE-EMPTY"). It expects an empty dictionary as a result.

    The function does not have a return value but asserts that the result is an empty dictionary. It also verifies that
    the request function was called once and the sleep function was not called.

    No exceptions are raised by this function.
    """

    client = JiraClient()

    # Simulate an empty response (no content in the body)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""  # Empty body
    mock_response.content = b""  # Empty content, simulating no body
    mock_response.json.return_value = {}  # Should not be called

    mock_request.return_value = mock_response

    # Call the function
    result = client.request("GET", "/rest/api/2/issue/ISSUE-EMPTY")

    # Ensure the result is an empty dictionary as per the logic
    assert result == {}
    mock_request.assert_called_once()
    mock_sleep.assert_not_called()


# Test Case: Handling RequestException (network failure) and ensuring coverage of the exception block
@patch("rest.client.time.sleep")
@patch("rest.client.requests.request")  # Mock the request to simulate a network failure
def test_request_request_exception(mock_request, mock_sleep):
    """
    This function initializes a JiraClient object for making requests to a Jira server.

    Arguments:
    - mock_request: A mock object for simulating HTTP requests.
    - mock_sleep: A mock object for simulating sleep time.

    Side Effects:
    - Initializes a JiraClient object for making requests to a Jira server.
    """

    client = JiraClient()

    # Simulate a RequestException being raised
    mock_request.side_effect = RequestException("Network error")

    # Call the function and check if the exception is raised
    with pytest.raises(JiraClientRequestError) as exc_info:
        client.request("GET", "/rest/api/2/issue/ISSUE-NETWORKERROR")

    # Verify that the JiraClientRequestError is raised with the correct message
    assert str(exc_info.value) == "Network error"

    # Ensure that the exception handling block is covered
    mock_request.assert_called_once()


# Test Case 2: Empty response text


@patch("rest.client.time.sleep")
@patch("rest.client.requests.request")  # Mock the request to simulate an empty response
def test_request_empty_response_text(mock_request, mock_sleep):
    """
    This function is a test function that simulates a request for empty response text from a Jira client. It takes two
    mock objects as arguments: mock_request and mock_sleep. The purpose of this function is to test the behavior of the
    JiraClient when it receives an empty response text. It initializes a JiraClient object but does not return any
    value.
    """

    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.json.return_value = {}  # shouldn't be called

    mock_request.return_value = mock_response

    result = client.request("GET", "/rest/api/2/issue/ISSUE-EMPTY")
    assert result == {}
    mock_request.assert_called_once()


# Test Case 3: Invalid JSON response
@patch("rest.client.time.sleep")
@patch(
    "rest.client.requests.request"
)  # Mock the request to simulate invalid JSON response
def test_request_invalid_json_response(mock_request, mock_sleep):
    """
    This function is a test function that simulates a request to a Jira API endpoint with invalid JSON response. It
    takes two mock objects as parameters: mock_request and mock_sleep. The purpose of this function is to test how the
    JiraClient class handles invalid JSON responses. It initializes a JiraClient object for testing purposes.
    """

    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>This is not JSON</html>"
    mock_response.json.side_effect = ValueError("No JSON")

    mock_request.return_value = mock_response

    result = client.request("GET", "/rest/api/2/issue/ISSUE-BADJSON")
    assert result == {}  # falls back to empty dict
    mock_request.assert_called_once()


# Test Case 4: HTTP 404 - Resource Not Found
@patch("rest.client.time.sleep")
@patch("rest.client.requests.request")  # Mock the request to simulate 404 error
def test_request_404_error(mock_request, mock_sleep):
    """
    Simulates a test scenario where a 404 error response is received during a request.

    Arguments:
    - mock_request: An object used to mock HTTP requests for testing purposes.
    - mock_sleep: An object used to mock sleep time for testing purposes.

    Side Effects:
    - Initializes a JiraClient object for further testing.
    """

    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.json.return_value = {}

    mock_request.return_value = mock_response

    with pytest.raises(JiraClientRequestError):
        client.request("GET", "/rest/api/2/issue/ISSUE-404")
    mock_request.call_count == 3


# Test Case 5: HTTP 401 - Unauthorized Access
@patch("rest.client.time.sleep")
@patch("rest.client.requests.request")  # Mock the request to simulate 401 error
def test_request_401_error(mock_request, mock_sleep):
    """
    This function is used to test the behavior of a JiraClient when it receives a 401 error during a request.

    Arguments:
    - mock_request: A mock object used to simulate the request behavior.
    - mock_sleep: A mock object used to simulate a sleep operation.

    Side Effects:
    - Initializes a JiraClient object.

    This function does not have a return value.
    """

    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.json.return_value = {}

    mock_request.return_value = mock_response

    with pytest.raises(JiraClientRequestError):
        client.request("GET", "/rest/api/2/issue/ISSUE-401")
    mock_request.call_count == 3


# Test Case 6: Client/Server error (HTTP 500)
@patch("rest.client.time.sleep")
@patch("rest.client.requests.request")  # Mock the request to simulate 500 error
def test_request_500_error(mock_request, mock_sleep):
    """
    This function tests the retry logic of a JiraClient object by simulating a 500 error response during an HTTP
    request.

    Arguments:
    - mock_request: A mock object used for simulating HTTP requests.
    - mock_sleep: A mock object used for simulating time delays.

    Side Effects:
    - Initializes a JiraClient object for testing purposes.
    """

    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.json.return_value = {}

    mock_request.return_value = mock_response

    with pytest.raises(JiraClientRequestError):
        client.request("GET", "/rest/api/2/issue/ISSUE-500")
    mock_request.call_count == 3


# Test Case 8: Multiple retries before failure (Test retry logic)
@patch("rest.client.time.sleep")
@patch(
    "rest.client.requests.request"
)  # Mock the request to simulate failure before success
def test_request_retry_logic(mock_request, mock_sleep):
    """
    This function initializes a JiraClient object for handling requests and retries.

    Arguments:
    - mock_request: A mock object for simulating HTTP requests.
    - mock_sleep: A mock object for simulating sleep time.
    """

    client = JiraClient()

    mock_response_1 = MagicMock()
    mock_response_1.status_code = 500
    mock_response_1.text = "Server error"

    mock_response_2 = MagicMock()
    mock_response_2.status_code = 500
    mock_response_2.text = "Server error"

    mock_response_3 = MagicMock()
    mock_response_3.status_code = 200
    mock_response_3.text = '{"key": "value"}'
    mock_response_3.json.return_value = {"key": "value"}

    mock_request.side_effect = [mock_response_1, mock_response_2, mock_response_3]

    result = client.request("GET", "/rest/api/2/issue/ISSUE-RETRY")
    assert result == {"key": "value"}
    assert mock_request.call_count == 3


# Test Case 1: Generate curl command with headers only (no data, no params)
@patch("builtins.print")  # Mock print to capture the generated curl command
def test_generate_curl_command_headers_only(mock_print):
    """
    Generate a cURL command with headers only.

    Arguments:
    - mock_print: A mock object used for printing messages.

    Side Effects:
    - Initializes a JiraClient object for interacting with Jira API.
    """

    client = JiraClient()

    method = "GET"
    url = "/rest/api/2/issue/ISSUE-123"
    headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    json_data = None
    params = None

    # Call the function
    client.generate_curl_command(method, url, headers, json_data, params)

    # Check if print was called with the correct command
    mock_print.assert_called_once()


# Test Case 2: Generate curl command with headers and JSON data
@patch("builtins.print")  # Mock print to capture the generated curl command
def test_generate_curl_command_with_json(mock_print):
    """
    Generate a cURL command with JSON data for testing purposes.

    Arguments:
    - mock_print: A mock object used for printing output.

    This function initializes a JiraClient object and generates a cURL command with the specified method, URL, headers,
    JSON data, and parameters for further testing.
    """

    client = JiraClient()

    method = "POST"
    url = "/rest/api/2/issue"
    headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    json_data = {"summary": "New issue", "description": "Description of the issue"}
    params = None

    # Call the function
    client.generate_curl_command(method, url, headers, json_data, params)

    # Check if print was called with the correct command
    mock_print.assert_called_once()


# Test Case 3: Generate curl command with headers and query parameters
@patch("builtins.print")  # Mock print to capture the generated curl command
def test_generate_curl_command_with_params(mock_print):
    """
    This function initializes a JiraClient object.

    Arguments:
    - mock_print: A mock object for printing (not used in the function).

    Side Effects:
    - Initializes a JiraClient object.
    """

    client = JiraClient()

    method = "GET"
    url = "/rest/api/2/issue"
    headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    json_data = None
    params = {"project": "TEST", "status": "open"}

    # Call the function
    client.generate_curl_command(method, url, headers, json_data, params)

    # Check if print was called with the correct command
    mock_print.assert_called_once()


# Test Case 4: Generate curl command with headers, JSON data, and query parameters
@patch("builtins.print")  # Mock print to capture the generated curl command
def test_generate_curl_command_all(mock_print):
    """
    Generate a cURL command for all requests made by a JiraClient.

    Arguments:
    - mock_print: A mock object for printing, used for testing purposes.

    Side Effects:
    - Initializes a JiraClient object for interacting with Jira.
    """

    client = JiraClient()

    method = "POST"
    url = "/rest/api/2/issue"
    headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    json_data = {"summary": "New issue", "description": "Description of the issue"}
    params = {"project": "TEST", "status": "open"}

    # Call the function
    client.generate_curl_command(method, url, headers, json_data, params)

    # Check if print was called with the correct command
    mock_print.assert_called_once()


# Test Case: All retry attempts fail, testing the final return statement
@patch("rest.client.requests.request")  # Mock the request to simulate failed responses
@patch(
    "rest.client.time.sleep"
)  # Mock time.sleep to prevent actual delays in retry logic
def test_request_final_return(mock_sleep, mock_request):
    """
    This function initializes a JiraClient object for making requests to a Jira server. It simulates failed attempts
    (500 errors) for all retry attempts to test the retry mechanism. The function does not take any arguments.

    Side Effects:
    - The function simulates retries by setting up mock responses with status code 500 and "Server error" text.
    - It uses mock objects to simulate requests and sleep.

    Exceptions:
    - The function raises a JiraClientRequestError when the JiraClient's _request method is called with a specific
    endpoint.

    The function ensures that the final result is an empty dictionary, verifies that the request was retried 3 times,
    and checks that the sleep function was called twice with a 2-second delay before retrying.
    """

    client = JiraClient()

    # Simulate failed attempts (500 errors) for all retry attempts
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 500
    mock_response_1.text = "Server error"

    mock_response_2 = MagicMock()
    mock_response_2.status_code = 500
    mock_response_2.text = "Server error"

    mock_response_3 = MagicMock()
    mock_response_3.status_code = 500
    mock_response_3.text = "Server error"

    # Define the side effects to simulate retries
    mock_request.side_effect = [mock_response_1, mock_response_2, mock_response_3]

    result = {}

    with pytest.raises(JiraClientRequestError):
        # Call the function
        result = client.request("GET", "/rest/api/2/issue/ISSUE-RETRY")

    # Ensure the final result is an empty dictionary
    assert result == {}

    # Verify that the request was retried 3 times
    assert mock_request.call_count == 3

    # Ensure sleep was called twice (after the first two failed attempts)
    mock_sleep.assert_called_with(2)  # Ensure that it waited 2 seconds before retrying
    assert mock_sleep.call_count == 2
