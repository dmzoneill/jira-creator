#!/usr/bin/env python
"""
This script defines a function 'unblock_issue' that unblocks a JIRA issue by updating the blocked_field and
reason_field in the issue payload. The function takes two parameters: request_fn, a function to make HTTP requests, and
issue_key, the key of the JIRA issue to unblock. The function constructs a payload with the updated fields and sends a
PUT request to the JIRA API to update the specified issue.

The 'unblock_issue' function takes 'request_fn' as a function parameter used to make requests to the JIRA API and
'issue_key' as a string parameter representing the key of the JIRA issue to unblock. It modifies the specified fields
in the JIRA issue to unblock it by updating the blocked_field and reason_field. The function constructs a payload with
the updated fields and sends a PUT request to the JIRA API to update the specified issue.
"""

from core.env_fetcher import EnvFetcher


def unblock_issue(request_fn, issue_key):
    """
    Unblocks a JIRA issue by updating the specified fields.

    Arguments:
    - request_fn (function): A function used to make requests to the JIRA API.
    - issue_key (str): The key of the JIRA issue to unblock.

    Side Effects:
    - Modifies the specified fields in the JIRA issue to unblock it.
    """

    blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD")
    reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

    payload = {}
    payload["fields"] = {}
    payload["fields"][blocked_field] = {}
    payload["fields"][blocked_field]["value"] = False
    payload["fields"][reason_field] = ""

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )
