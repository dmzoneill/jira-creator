#!/usr/bin/env python
"""
Sets acceptance criteria for a Jira issue.

Arguments:
- jira (JIRA): A JIRA instance used to interact with Jira API.
- args (Namespace): A namespace containing parsed arguments.

Return:
- bool: True if acceptance criteria were successfully set.

Exceptions:
- SetAcceptanceCriteriaError: If an error occurs while setting acceptance criteria.

Side Effects:
- Modifies the acceptance criteria for the specified Jira issue.
- Prints a success message if the acceptance criteria are set successfully.
- Prints an error message if setting acceptance criteria fails.
"""
from argparse import Namespace

from exceptions.exceptions import SetAcceptanceCriteriaError
from rest.client import JiraClient


def cli_set_acceptance_criteria(jira: JiraClient, args: Namespace) -> bool:
    """
    Sets acceptance criteria for a Jira issue.

    Arguments:
    - jira (JIRA): A JIRA instance used to interact with Jira API.
    - args (Namespace): A namespace containing parsed arguments.

    Return:
    - bool: True if acceptance criteria were successfully set.

    Exceptions:
    - SetAcceptanceCriteriaError: If an error occurs while setting acceptance criteria.

    Side Effects:
    - Modifies the acceptance criteria for the specified Jira issue.
    - Prints a success message if the acceptance criteria are set successfully.
    - Prints an error message if setting acceptance criteria fails.
    """

    if not isinstance(args.issue_key, str) or not args.issue_key.strip():
        raise ValueError("Invalid issue key provided.")

    if (
        not isinstance(args.acceptance_criteria, str)
        or not args.acceptance_criteria.strip()
    ):
        raise ValueError("Invalid acceptance criteria provided.")

    try:
        jira.set_acceptance_criteria(args.issue_key, args.acceptance_criteria)
        print(f"✅ Acceptance criteria set to '{args.acceptance_criteria}'")
        return True
    except SetAcceptanceCriteriaError as e:
        msg = f"❌ Failed to set acceptance criteria: {str(e)}"
        print(msg)
        raise SetAcceptanceCriteriaError(msg) from e
    except Exception as e:
        msg = f"❌ An unexpected error occurred: {str(e)}"
        print(msg)
        raise SetAcceptanceCriteriaError(e) from e
