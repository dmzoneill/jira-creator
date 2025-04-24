#!/usr/bin/env python
"""
This script defines a test function 'test_set_acceptance_criteria' that tests the functionality of setting acceptance
criteria for a JIRA issue using a provided client. The function simulates GET and PUT responses, calls the
'set_acceptance_criteria' method of the client, captures the output, and asserts that the output contains an expected
success message. The test function takes 'capsys' and 'client' as parameters and utilizes a mocked client request.

The 'test_set_acceptance_criteria' function sets acceptance criteria for a specified test issue identified by
'issue_key'.
It takes 'capsys' as a pytest fixture for capturing stdout and stderr output, and 'client' as an instance of the client
used to interact with the issue tracking system. The function has the side effect of setting the acceptance criteria for
the test issue.
"""

from core.env_fetcher import EnvFetcher


def test_set_acceptance_criteria(capsys, client):
    """
    Set acceptance criteria for a specified test issue.

    Arguments:
    - capsys: A pytest fixture for capturing stdout and stderr output.
    - client: An instance of the client used to interact with the issue tracking system.

    Side Effects:
    - Sets the acceptance criteria for a test issue identified by 'issue_key'.
    """

    issue_key = "AAP-test_set_acceptance_criteria"
    acceptance_criteria = "Acceptance criteria description"

    # Simulate the GET and PUT responses correctly
    client.request.side_effect = [
        {
            "fields": {
                EnvFetcher.get(
                    "JIRA_ACCEPTANCE_CRITERIA_FIELD"
                ): "Acceptance criteria description"
            }
        },  # GET response with 'fields'
        {},  # PUT response (successful)
    ]

    # Call the set_acceptance_criteria method
    client.set_acceptance_criteria(issue_key, acceptance_criteria)

    # Capture the output printed by the function
    captured = capsys.readouterr().out

    # Assert that the output contains the expected success message
    assert f"✅ Updated acceptance criteria of {issue_key}" in captured
