#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) function for fetching and displaying blocked issues from a Jira
project.

The primary function, `cli_blocked`, interfaces with the Jira API to retrieve issues based on specified criteria,
including project, component, and optionally user. It handles the display of blocked issues, showing relevant details
such as issue key, status, assignee, reason, and summary. If no issues are found, it notifies the user accordingly. The
function also manages exceptions by raising a `ListBlockedError` when an error occurs during the issue retrieval
process.

Note: Sections of code marked with 'jscpd:ignore-start' and 'jscpd:ignore-end' are excluded from code duplication
checks.
"""

from argparse import Namespace
from typing import Any, Dict, List, Union

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListBlockedError
from rest.client import JiraClient


# /* jscpd:ignore-start */
def cli_blocked(jira: JiraClient, args: Namespace) -> Union[List[Dict[str, Any]], bool]:
    """
    Retrieve a list of blocked issues from Jira based on specified criteria.

    Arguments:
    - jira (JIRA): An instance of the JIRA API client.
    - args (Namespace): An object containing the following attributes:
    - project (str): The project key to filter the blocked issues.
    - component (str): The component to filter the blocked issues.
    - user (str, optional): The user to filter the blocked issues. If not provided, the current user will be used.

    Return:
    - list: A list of blocked issues retrieved based on the specified criteria or True if no issues found.

    Exceptions:
    - ListBlockedError: Raised when there is an error listing blocked issues.

    Side Effects:
    - Prints information about the retrieved blocked issues and status messages.
    """

    try:
        issues = jira.list_issues(
            project=args.project,
            component=args.component,
            assignee=args.user or jira.get_current_user(),
        )

        if not issues:
            print("✅ No issues found.")
            return True

        blocked_issues: List[Dict[str, Union[str, None]]] = []
        for issue in issues:
            fields = issue["fields"]
            is_blocked = (
                fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value")
                == "True"
            )
            if is_blocked:
                blocked_issues.append(
                    {
                        "key": issue["key"],
                        "status": fields["status"]["name"],
                        "assignee": (
                            fields["assignee"]["displayName"]
                            if fields["assignee"]
                            else "Unassigned"
                        ),
                        "reason": fields.get(
                            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"), "(no reason)"
                        ),
                        "summary": fields["summary"],
                    }
                )

        if not blocked_issues:
            print("✅ No blocked issues found.")
            return True

        print("🔒 Blocked issues:")
        print("-" * 80)
        for i in blocked_issues:
            print(f"{i['key']} [{i['status']}] — {i['assignee']}")
            print(f"  🔸 Reason: {i['reason']}")
            print(f"  📄 {i['summary']}")
            print("-" * 80)

        return blocked_issues

    except ListBlockedError as e:
        msg = f"❌ Failed to list blocked issues: {e}"
        print(msg)
        raise ListBlockedError(e) from e


# /* jscpd:ignore-end */
