#!/usr/bin/env python
"""
This script defines a function 'cli_migrate' that migrates an issue in Jira to a new issue type.
It takes Jira instance and command line arguments as input, migrates the issue, and prints the migration details.
If the migration fails, it raises a MigrateError with an appropriate error message.

Function:
- cli_migrate(jira, args)
Migrate an issue in Jira to a new type.

Arguments:
- jira (JiraClient): An instance of the Jira client.
- args (Namespace): A namespace containing the following attributes:
- issue_key (str): The key of the issue to be migrated.
- new_type (str): The new type to migrate the issue to.

Return:
- str: The new key of the migrated issue.

Exceptions:
- MigrateError: Raised if the migration process fails.

Side Effects:
- Prints the success message if the migration is successful.
- Prints the error message if the migration fails.
"""

from argparse import Namespace

from exceptions.exceptions import MigrateError
from rest.client import JiraClient


def cli_migrate(jira: JiraClient, args: Namespace) -> str:
    """
    Migrate an issue in Jira to a new type.

    Arguments:
    - jira (JiraClient): An instance of the Jira client.
    - args (Namespace): A namespace containing the following attributes:
    - issue_key (str): The key of the issue to be migrated.
    - new_type (str): The new type to migrate the issue to.

    Return:
    - str: The new key of the migrated issue.

    Exceptions:
    - MigrateError: Raised if the migration process fails.

    Side Effects:
    - Prints the success message if the migration is successful.
    - Prints the error message if the migration fails.
    """

    try:
        new_key: str = jira.migrate_issue(args.issue_key, args.new_type)
        print(
            f"✅ Migrated {args.issue_key} to {new_key}: {jira.jira_url}/browse/{new_key}"
        )
        return new_key
    except MigrateError as e:
        msg: str = f"❌ Migration failed: {e}"
        print(msg)
        raise MigrateError(e) from e
