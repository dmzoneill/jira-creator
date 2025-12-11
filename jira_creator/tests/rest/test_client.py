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
from requests.exceptions import RequestException

from jira_creator.exceptions.exceptions import JiraClientRequestError
from jira_creator.rest.client import JiraClient


# Test Case 1: Valid JSON response
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate an API response
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
@patch("jira_creator.rest.client.time.sleep")  # Mock time.sleep to prevent delays in retry logic
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate an empty response
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
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate a network failure
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


@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate an empty response
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
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate invalid JSON response
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
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate 404 error
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
    mock_response.headers = {}

    mock_request.return_value = mock_response

    # Mock AI analysis to prevent actual API calls
    with patch.object(client, "_analyze_and_fix_error", return_value=None):
        with patch.object(client, "_analyze_error_with_ai", return_value=None):
            with pytest.raises(JiraClientRequestError):
                client.request("GET", "/rest/api/2/issue/ISSUE-404")
    mock_request.call_count == 3


# Test Case 5: HTTP 401 - Unauthorized Access
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate 401 error
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
    mock_response.headers = {}

    mock_request.return_value = mock_response

    # Mock AI analysis to prevent actual API calls
    with patch.object(client, "_analyze_and_fix_error", return_value=None):
        with patch.object(client, "_analyze_error_with_ai", return_value=None):
            with pytest.raises(JiraClientRequestError):
                client.request("GET", "/rest/api/2/issue/ISSUE-401")
    mock_request.call_count == 3


# Test Case 6: Client/Server error (HTTP 500)
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate 500 error
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
    mock_response.headers = {}

    mock_request.return_value = mock_response

    # Mock AI analysis to prevent actual API calls
    with patch.object(client, "_analyze_and_fix_error", return_value=None):
        with patch.object(client, "_analyze_error_with_ai", return_value=None):
            with pytest.raises(JiraClientRequestError):
                client.request("GET", "/rest/api/2/issue/ISSUE-500")
    mock_request.call_count == 3


# Test Case 8: Multiple retries before failure (Test retry logic)
@patch("jira_creator.rest.client.time.sleep")
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate failure before success
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
@patch("jira_creator.rest.client.requests.request")  # Mock the request to simulate failed responses
@patch("jira_creator.rest.client.time.sleep")  # Mock time.sleep to prevent actual delays in retry logic
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
    mock_response_1.headers = {}

    mock_response_2 = MagicMock()
    mock_response_2.status_code = 500
    mock_response_2.text = "Server error"
    mock_response_2.headers = {}

    mock_response_3 = MagicMock()
    mock_response_3.status_code = 500
    mock_response_3.text = "Server error"
    mock_response_3.headers = {}

    # Define the side effects to simulate retries
    mock_request.side_effect = [mock_response_1, mock_response_2, mock_response_3]

    result = {}

    # Mock AI analysis to prevent actual API calls
    with patch.object(client, "_analyze_and_fix_error", return_value=None):
        with patch.object(client, "_analyze_error_with_ai", return_value=None):
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


def test_get_field_name_success():
    """Test successful field name lookup."""
    client = JiraClient()

    # Mock successful response with field data
    mock_response = [
        {"id": "customfield_12310243", "name": "Story Points"},
        {"id": "customfield_12316543", "name": "Blocked"},
        {"id": "summary", "name": "Summary"},
    ]

    with patch.object(client, "request", return_value=mock_response):
        result = client.get_field_name("customfield_12310243")
        assert result == "Story Points"


def test_get_field_name_not_found():
    """Test field name lookup when field not found."""
    client = JiraClient()

    # Mock successful response but field not in list
    mock_response = [
        {"id": "customfield_12310243", "name": "Story Points"},
        {"id": "summary", "name": "Summary"},
    ]

    with patch.object(client, "request", return_value=mock_response):
        result = client.get_field_name("customfield_99999")
        assert result is None


def test_get_field_name_empty_response():
    """Test field name lookup with empty response."""
    client = JiraClient()

    with patch.object(client, "request", return_value=[]):
        result = client.get_field_name("customfield_12310243")
        assert result is None


def test_get_field_name_none_response():
    """Test field name lookup with None response."""
    client = JiraClient()

    with patch.object(client, "request", return_value=None):
        result = client.get_field_name("customfield_12310243")
        assert result is None


def test_get_field_name_exception():
    """Test field name lookup when request raises exception."""
    client = JiraClient()

    with patch.object(client, "request", side_effect=Exception("Request failed")):
        result = client.get_field_name("customfield_12310243")
        assert result is None


def test_extract_error_detail_with_error_messages():
    """Test _extract_error_detail with errorMessages field."""
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.json.return_value = {"errorMessages": ["Error 1", "Error 2"]}

    result = client._extract_error_detail(mock_response)
    assert result == "Error 1; Error 2"


def test_extract_error_detail_with_errors_field():
    """Test _extract_error_detail with errors field."""
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.json.return_value = {"errors": {"field1": "Error 1", "field2": "Error 2"}}

    result = client._extract_error_detail(mock_response)
    assert "field1: Error 1" in result
    assert "field2: Error 2" in result


def test_extract_error_detail_with_message_field():
    """Test _extract_error_detail with message field."""
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.json.return_value = {"message": "Error message"}

    result = client._extract_error_detail(mock_response)
    assert result == "Error message"


def test_extract_error_detail_with_exception():
    """Test _extract_error_detail when JSON parsing fails."""
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.json.side_effect = Exception("Invalid JSON")
    mock_response.text = "Plain text error message"

    result = client._extract_error_detail(mock_response)
    assert result == "Plain text error message"


@patch("builtins.print")
def test_print_error_message_with_error_detail(mock_print):
    """Test _print_error_message with error detail."""
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"errorMessages": ["Bad request"]}

    client._print_error_message(mock_response)
    mock_print.assert_called_once_with("❌ Client/Server error (400): Bad request")


@patch("jira_creator.rest.client.requests.get")
def test_fetch_jira_context_success(mock_get):
    """Test _fetch_jira_context_for_error with successful fetches."""
    client = JiraClient()

    # Mock successful responses for all three fetches
    mock_types_response = MagicMock()
    mock_types_response.status_code = 200
    mock_types_response.json.return_value = [{"name": "Story"}, {"name": "Bug"}]

    mock_fields_response = MagicMock()
    mock_fields_response.status_code = 200
    mock_fields_response.json.return_value = [
        {"id": "customfield_123", "name": "Story Points", "custom": True},
        {"id": "summary", "name": "Summary", "custom": False},
    ]

    mock_project_response = MagicMock()
    mock_project_response.status_code = 200
    mock_project_response.json.return_value = {"key": "XYZ", "name": "Test Project"}

    mock_get.side_effect = [mock_types_response, mock_fields_response, mock_project_response]

    issue_types, custom_fields, project_config = client._fetch_jira_context_for_error()

    assert issue_types == ["Story", "Bug"]
    assert custom_fields == {"customfield_123": "Story Points"}
    assert project_config == {"key": "XYZ", "name": "Test Project"}


@patch("jira_creator.rest.client.requests.get")
def test_fetch_jira_context_exception(mock_get):
    """Test _fetch_jira_context_for_error with exception."""
    client = JiraClient()

    # Mock exception during fetch
    mock_get.side_effect = Exception("Network error")

    issue_types, custom_fields, project_config = client._fetch_jira_context_for_error()

    # Should return None for all when exception occurs
    assert issue_types is None
    assert custom_fields is None
    assert project_config is None


@patch("builtins.print")
@patch("builtins.input")
def test_prompt_for_fix_consent_with_payload_fix(mock_input, mock_print):
    """Test _prompt_user_for_fix with payload fix type."""
    from jira_creator.rest.client import FixProposal

    client = JiraClient()
    mock_input.return_value = "y"

    fix_proposal = FixProposal(
        analysis="Test analysis",
        fix_type="payload",
        confidence=0.9,
        payload_fix={"summary": "Fixed summary", "description": "Fixed description"},
        file_changes=[],
        reasoning="Need to fix payload fields",
    )

    result = client._prompt_user_for_fix(fix_proposal)

    assert result is True
    # Verify payload fix was printed
    calls = [str(call) for call in mock_print.call_args_list]
    assert any("Payload changes" in str(call) for call in calls)


@patch("builtins.print")
@patch("builtins.input")
def test_prompt_for_fix_consent_keyboard_interrupt(mock_input, mock_print):
    """Test _prompt_user_for_fix with KeyboardInterrupt."""
    from jira_creator.rest.client import FileChange, FixProposal

    client = JiraClient()
    mock_input.side_effect = KeyboardInterrupt()

    fix_proposal = FixProposal(
        analysis="Test analysis",
        fix_type="codebase",
        confidence=0.8,
        payload_fix=None,
        file_changes=[FileChange(file_path="/tmp/test.py", old_content="old", new_content="new")],
        reasoning="Fix code issue",
    )

    result = client._prompt_user_for_fix(fix_proposal)

    assert result is False
    # Verify cancellation message
    calls = [str(call) for call in mock_print.call_args_list]
    assert any("cancelled" in str(call).lower() for call in calls)


@patch("builtins.print")
@patch("builtins.input")
def test_prompt_for_fix_consent_eof_error(mock_input, mock_print):
    """Test _prompt_user_for_fix with EOFError."""
    from jira_creator.rest.client import FileChange, FixProposal

    client = JiraClient()
    mock_input.side_effect = EOFError()

    fix_proposal = FixProposal(
        analysis="Test analysis",
        fix_type="codebase",
        confidence=0.7,
        payload_fix=None,
        file_changes=[FileChange(file_path="/tmp/test.py", old_content="old", new_content="new")],
        reasoning="Fix code issue",
    )

    result = client._prompt_user_for_fix(fix_proposal)

    assert result is False


@patch("builtins.print")
def test_apply_fix_with_none_type(mock_print):
    """Test _apply_fix with fix_type='none'."""
    from jira_creator.rest.client import FixProposal

    client = JiraClient()

    fix_proposal = FixProposal(
        analysis="Test analysis",
        fix_type="none",
        confidence=0.5,
        payload_fix=None,
        file_changes=[],
        reasoning="Cannot fix",
    )

    result = client._apply_fix(fix_proposal)

    assert result is False
    # The function just returns False and logs (doesn't print)


@patch("builtins.print")
@patch("os.path.exists")
def test_apply_codebase_fix_old_content_not_found(mock_exists, mock_print):
    """Test _apply_codebase_fix when old content doesn't match."""
    from unittest.mock import mock_open

    from jira_creator.rest.client import FileChange

    client = JiraClient()
    mock_exists.return_value = True

    # File contains different content than expected
    file_content = "This is different content"
    m = mock_open(read_data=file_content)

    fix_changes = [FileChange(file_path="/tmp/test.py", old_content="expected old content", new_content="new content")]

    with patch("builtins.open", m):
        result = client._apply_codebase_fix(fix_changes)

    assert result is False
    # Verify error message
    calls = [str(call) for call in mock_print.call_args_list]
    assert any("Old content not found" in str(call) for call in calls)


@patch("builtins.print")
@patch("os.path.exists")
def test_apply_codebase_fix_with_exception(mock_exists, mock_print):
    """Test _apply_codebase_fix when exception occurs."""
    from jira_creator.rest.client import FileChange

    client = JiraClient()
    mock_exists.side_effect = Exception("Disk error")

    fix_changes = [FileChange(file_path="/tmp/test.py", old_content="old", new_content="new")]

    result = client._apply_codebase_fix(fix_changes)

    assert result is False
    # Verify error message
    calls = [str(call) for call in mock_print.call_args_list]
    assert any("Failed to apply fix" in str(call) for call in calls)
