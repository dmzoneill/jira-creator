#!/usr/bin/env python
"""
This module provides tools for linting Jira issues and presenting the results in a well-structured table format.

It contains two primary functions:

1. `print_status_table(failure_statuses)`:
- Displays a formatted table of failure statuses.
- Normalizes status values for better readability using visual indicators.

2. `cli_lint_all(jira, ai_provider, args)`:
- Lints Jira issues based on command-line arguments such as project, component, reporter, or assignee.
- Validates issues retrieved from Jira using an AI provider and summarizes the results.
- Outputs the status of each issue, indicating which passed or failed lint checks, along with detailed feedback for any
failures.

Exceptions:
- Raises `LintAllError` if there is a failure during the linting process.

This module is intended for use in a command-line interface (CLI) environment, allowing users to validate and receive
formatted feedback on Jira issues.
"""

# pylint: disable=too-many-locals

import textwrap
from argparse import Namespace
from collections import OrderedDict
from typing import Any, Dict, List, Tuple, Union

from commands.cli_validate_issue import cli_validate_issue as validate
from exceptions.exceptions import LintAllError
from providers.ai_provider import AIProvider
from rest.client import JiraClient


def print_status_table(
    failure_statuses: List[Dict[str, Union[str, bool, None]]],
) -> None:
    """
    Collects all unique keys from all rows in the failure_statuses table.

    Arguments:
    - failure_statuses (list of dict): A list of dictionaries representing failure statuses.

    Returns:
    None
    """

    # Step 1: Collect all unique keys from all rows
    all_keys = set()
    for row in failure_statuses:
        all_keys.update(row.keys())

    # Step 2: Ensure each row contains all the keys
    for row in failure_statuses:
        for key in all_keys:
            row.setdefault(key, None)

    # Step 3: Normalize the values in failure_statuses
    for row in failure_statuses:
        for key, value in row.items():
            if value is True:
                row[key] = "✅"  # Green check for True
            elif value is False:
                row[key] = "❌"  # Red cross for False
            elif value is None or value == "?":
                row[key] = "❎"  # Question mark for None or "?"

    # Step 4: Count the number of "❌" (representing False) in each row
    failure_statuses.sort(key=lambda row: row.get("jira_issue_id", ""))

    # Step 5: Get headers and calculate column widths based on header lengths
    headers = list(all_keys)

    headers.sort()  # Sort alphabetically
    if "jira_issue_id" in headers:
        headers.remove("jira_issue_id")  # Remove jira_issue_id from sorted list
        headers.insert(0, "jira_issue_id")  # Insert it at the beginning

    column_widths: Dict[str, int] = {}

    # Calculate column widths based only on the header length
    for header in headers:
        column_widths[header] = len(header)

    # Step 6: Print the table
    print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

    print(
        "| "
        + " | ".join(f"{header}".ljust(column_widths[header]) for header in headers)
        + " |"
    )
    print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

    for row in failure_statuses:
        formatted_row = ""
        for header in headers:
            value = str(row.get(header, "?"))
            formatted_row += f"| {value.ljust(column_widths[header])}"

        print(formatted_row + "|")

    print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")


def cli_lint_all(
    jira: JiraClient, ai_provider: AIProvider, args: Namespace
) -> List[Dict[str, Any]]:
    """
    Lint all Jira issues based on specified criteria.

    Arguments:
    - jira (JiraClient): An instance of the JIRA client.
    - ai_provider (AIProvider): An instance of the AI provider.
    - args (Namespace): A namespace object containing parsed command-line arguments.
    - args.reporter (str): The reporter of the issues to filter by.
    - args.assignee (str): The assignee of the issues to filter by.
    - args.project (str): The project key to filter the issues.
    - args.component (str): The component to filter the issues.

    Exceptions:
    - LintAllError: Raised if there is an issue during the linting process.
    """

    try:
        if args.reporter:
            issues = jira.list_issues(
                project=args.project, component=args.component, reporter=args.reporter
            )
        elif args.assignee:
            issues = jira.list_issues(
                project=args.project, component=args.component, assignee=args.assignee
            )
        else:
            issues = jira.list_issues(project=args.project, component=args.component)

        if not issues:
            print("✅ No issues assigned to you.")
            return []

        failures: Dict[str, Tuple[str, List[str]]] = {}
        failure_statuses: List[Dict[str, Any]] = []

        for issue in issues:
            key = issue["key"]
            full_issue = jira.request("GET", f"/rest/api/2/issue/{key}")
            fields = full_issue["fields"]
            fields["key"] = issue["key"]
            summary = fields["summary"]

            problems, statuses = validate(fields, ai_provider)
            statuses = OrderedDict(statuses)
            statuses = OrderedDict([("jira_issue_id", key)] + list(statuses.items()))
            failure_statuses.append(statuses)

            if len(problems) > 0:
                failures[key] = (summary, problems)
                print(f"❌ {key} {summary} failed lint checks")
            else:
                print(f"✅ {key} {summary} passed")

        if not failures:
            print("\n🎉 All issues passed lint checks!")
        else:
            print("\n⚠️ Issues with lint problems:")
            for key, (summary, problems) in failures.items():
                print(f"\n🔍 {key} - {summary}")
                for p in problems:
                    wrapped_text = textwrap.fill(p, width=120, break_long_words=False)
                    print(f" - {wrapped_text}")

            print_status_table(failure_statuses)
        return failure_statuses
    except LintAllError as e:
        msg = f"❌ Failed to lint issues: {e}"
        print(msg)
        raise LintAllError(e) from e
