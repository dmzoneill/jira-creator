#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) function for searching JIRA issues using JIRA Query Language (JQL).

The `cli_search` function allows users to search for issues based on a specified JQL query through a JIRA client
instance. It retrieves relevant issue fields and displays the results in a formatted table. The function includes error
handling for search-related exceptions to ensure appropriate messages are displayed when issues arise.

Functions:
- cli_search(jira, args): Executes a search for issues in JIRA using the provided JQL query.

Arguments:
- jira: A JIRA client object for API communication.
- args: An object containing parsed command-line arguments, which must include a 'jql' attribute representing the JQL
query.

Exceptions:
- The function may raise exceptions related to the JIRA API or invalid queries.

Note:
- This script depends on external modules such as 'core.env_fetcher' and 'exceptions.exceptions' for environment
variable fetching and exception handling, respectively.
"""

import re
from typing import Any, List, Tuple, Union
from rest.client import JiraClient
from argparse import Namespace

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import SearchError


def cli_search(jira: JiraClient, args: Namespace) -> Union[List[Any], bool]:
    """
    Search for issues in Jira based on the provided JQL query.

    Arguments:
    - jira: A Jira client object used to communicate with the Jira API.
    - args: An object containing the parsed command-line arguments.
    It should have a 'jql' attribute representing the Jira Query Language query.

    Exceptions:
    - This function may raise exceptions related to the Jira API or invalid queries.

    Note: This function interacts with the Jira API to search for issues based on the provided JQL query.
    """

    try:
        jql: str = args.jql
        issues: List[dict] = jira.search_issues(jql)

        if issues is None or len(issues) == 0:
            print("❌ No issues found for the given JQL.")
            return False

        rows: List[Tuple[str, str, str, str, str, str, str]] = []
        for issue in issues:
            f: dict = issue["fields"]
            sprints: List[str] = f.get(EnvFetcher.get("JIRA_SPRINT_FIELD"), [])
            sprint: str = next(
                (
                    re.search(r"name=([^,]+)", s).group(1)
                    for s in sprints
                    if "state=ACTIVE" in s and "name=" in s
                ),
                "—",
            )

            rows.append(
                (
                    issue["key"],
                    f["status"]["name"],
                    f["assignee"]["displayName"] if f["assignee"] else "Unassigned",
                    f.get("priority", {}).get("name", "—"),
                    str(f.get(EnvFetcher.get("JIRA_STORY_POINTS_FIELD"), "—")),
                    sprint,
                    f["summary"],
                )
            )

        rows.sort(key=lambda r: (r[5], r[1]))

        headers: List[str] = [
            "Key",
            "Status",
            "Assignee",
            "Priority",
            "Points",
            "Sprint",
            "Summary",
        ]
        widths: List[int] = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]

        header_fmt: str = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_fmt)
        print("-" * len(header_fmt))

        for r in rows:
            print(" | ".join(val.ljust(widths[i]) for i, val in enumerate(r)))

        return issues
    except SearchError as e:
        msg: str = f"❌ Failed to search issues: {e}"
        print(msg)
        raise SearchError(e) from e