#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) function to list issues from a Jira project.

The `cli_list_issues` function retrieves and displays issues based on various filtering options such as project,
component, reporter, assignee, status, summary, and blocked status. It formats the output into a tabular structure,
ensuring that the summary column is limited to a specified width for better readability.

The function handles potential errors related to listing issues and prints appropriate messages to the console.

Dependencies:
- `re`: For regular expression operations.
- `core.env_fetcher`: To fetch environment variables related to Jira fields.
- `exceptions.exceptions`: Custom exceptions for error handling.

Usage:
- Call `cli_list_issues(jira, args)` where `jira` is the Jira client instance and `args` contains the filtering
criteria.
"""

import re
from typing import List, Tuple, Any
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListIssuesError
from rest.client import JiraClient
from argparse import Namespace


def cli_list_issues(jira: JiraClient, args: Namespace) -> List[Any]:
    """
    Retrieve a list of issues from a Jira instance based on the provided arguments.

    Arguments:
    - jira (Any): An instance of the Jira client used to interact with the Jira API.
    - args (Any): A Namespace object containing the following attributes:
    - project (str): The project key for filtering the issues.
    - component (str): The component name for filtering the issues.
    - reporter (str): The reporter's username for filtering the issues.
    - assignee (str): The assignee's username for filtering the issues.
    - status (str): The status to filter the issues by.
    - summary (str): A keyword to filter the issues by their summary.
    - blocked (bool): A flag to filter for blocked issues.
    - unblocked (bool): A flag to filter for unblocked issues.

    Side Effects:
    - Calls the 'list_issues' method of the Jira client to fetch a list of issues based on the provided arguments.
    - Depending on the presence of the 'reporter' attribute in 'args', the issues are filtered by either 'reporter' or
    'assignee'.
    - Prints a formatted table of the filtered issues to the console.

    Exceptions:
    - Raises ListIssuesError if the attempt to list issues fails.
    """

    try:
        issues = jira.list_issues(
            project=args.project,
            component=args.component,
            reporter=args.reporter if args.reporter else None,
            assignee=args.assignee if not args.reporter else None,
        )

        if not issues:
            print("No issues found.")
            return []

        rows: List[Tuple[str, str, str, str, str, str, str]] = []
        for issue in issues:
            f = issue["fields"]
            sprints = f.get(EnvFetcher.get("JIRA_SPRINT_FIELD"), [])
            sprint = next(
                (
                    re.search(r"name=([^,]+)", s).group(1)
                    for s in sprints
                    if "state=ACTIVE" in s and "name=" in s
                ),
                "—",
            )

            if (
                args.status
                and args.status.lower() not in f.get("status", {}).get("name", "").lower()
            ):
                continue
            if (
                args.summary
                and args.summary.lower() not in f.get("summary", "").lower()
            ):
                continue
            if args.blocked and f.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}):
                continue
            if (
                args.unblocked
                and f.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}) is False
            ):
                continue

            rows.append(
                (
                    issue["key"],
                    f["status"]["name"],
                    f["assignee"]["displayName"] if f.get("assignee") else "Unassigned",
                    f.get("priority", {}).get("name", "—"),
                    str(f.get(EnvFetcher.get("JIRA_STORY_POINTS_FIELD"), "—")),
                    sprint,
                    f["summary"],
                )
            )

        rows.sort(key=lambda r: (r[5], r[1]))

        headers = [
            "Key",
            "Status",
            "Assignee",
            "Priority",
            "Points",
            "Sprint",
            "Summary",
        ]

        max_summary_length = 60
        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]

        widths[6] = min(widths[6], max_summary_length)

        header_fmt = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_fmt)
        print("-" * len(header_fmt))

        truncate_length = 97

        for r in rows:
            r = list(r)

            if len(r[6]) > max_summary_length:
                r[6] = r[6][:truncate_length] + " .."

            print(" | ".join(val.ljust(widths[i]) for i, val in enumerate(r)))
        return issues
    except ListIssuesError as e:
        msg = f"❌ Failed to list issues: {e}"
        print(msg)
        raise