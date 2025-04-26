#!/usr/bin/env python
"""
This module provides a command-line interface for editing Jira issue descriptions. It allows users to fetch, edit,
lint, and update descriptions while ensuring quality through validation checks. The module integrates with an AI
provider for enhanced description improvement.

Key Functions:
- fetch_description(jira, issue_key): Retrieves the description of a specified Jira issue.
- edit_description(original_description): Opens the issue description in a text editor for user modifications.
- get_prompt(jira, issue_key, default_prompt): Retrieves a prompt based on the issue type.
- lint_description_once(cleaned, ai_provider): Validates the cleaned description and prompts for additional input if
issues are found.
- lint_description(cleaned, ai_provider): Continuously lints the description until no issues are detected.
- update_jira_description(jira, issue_key, cleaned): Updates the Jira issue description with the cleaned text.
- cli_edit_issue(jira, ai_provider, default_prompt, try_cleanup_fn, args): Main function coordinating the description
editing process.

Exceptions:
- Various exceptions are raised for error handling, including issues related to editing, fetching, and updating
descriptions.
"""

import os
import subprocess
import tempfile
from argparse import Namespace
from typing import Any, Tuple

from rest.client import JiraClient
from rest.prompts import IssueType, PromptLibrary

from exceptions.exceptions import (  # isort: skip
    EditDescriptionError,
    EditIssueError,
    FetchDescriptionError,
    GetPromptError,
    UpdateDescriptionError,
)  # isort: skip

from commands.cli_validate_issue import cli_validate_issue as validate  # isort: skip


def fetch_description(jira: JiraClient, issue_key: Namespace) -> str:
    """
    Fetches the description of a Jira issue identified by the given issue key.

    Args:
    jira (JiraAPI): An instance of JiraAPI used to interact with the Jira service.
    issue_key (str): The key identifying the Jira issue for which the description needs to be fetched.

    Returns:
    str: The description of the Jira issue.

    Raises:
    FetchDescriptionError: If an error occurs while fetching the description.
    """

    try:
        print("Fetching description...")
        return jira.get_description(issue_key)
    except FetchDescriptionError as e:
        msg = f"❌ Failed to fetch description: {e}"
        print(msg)
        raise FetchDescriptionError(e) from e


def edit_description(original_description: str) -> str:
    """
    Edit the description using the default text editor.

    Arguments:
    - original_description (str): The original description to be edited.

    Return:
    - str: The edited description after modifications.

    Exceptions:
    - EditDescriptionError: Raised if an error occurs while editing the description.

    Side Effects:
    - Opens the default text editor to allow the user to modify the description.
    - Prints an error message if editing the description fails, which is captured in the logs.
    """

    try:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write(original_description or "")
            tmp.flush()
            subprocess.call(
                [os.environ.get("EDITOR", "vim"), tmp.name]
            )  # This can raise an exception
            tmp.seek(0)
            return tmp.read()
    except EditDescriptionError as e:
        error_message = f"❌ Failed to edit description: {e}"
        print(error_message)  # This would be captured in the logs
        raise EditDescriptionError(e) from e


def get_prompt(jira: Any, issue_key: str, default_prompt: str) -> str:
    """
    Retrieve a prompt related to a Jira issue.

    Arguments:
    - jira: An object representing the Jira instance.
    - issue_key: A string containing the key of the Jira issue.
    - default_prompt: A string representing the default prompt to be used if the Jira prompt cannot be retrieved.

    Return:
    - A string containing the prompt related to the Jira issue. If the prompt cannot be retrieved, the default prompt
    is returned.

    Exceptions:
    - GetPromptError: Raised if there is an error while trying to retrieve the Jira prompt.

    Side Effects:
    - Prints a message if the Jira prompt cannot be retrieved and the default prompt is used.
    """

    try:
        print("Getting Jira prompt...")
        return PromptLibrary.get_prompt(
            IssueType(jira.get_issue_type(issue_key).lower())
        )
    except GetPromptError:
        print("❌ Failed to get Jira prompt, using default prompt.")
        return default_prompt


def lint_description_once(cleaned: str, ai_provider: Any) -> Tuple[str, bool]:
    """
    Lint a description once using a specified AI provider.

    Arguments:
    - cleaned (str): The cleaned description to be linted.
    - ai_provider (Any): The AI provider to use for linting.

    Side Effects:
    - Prints the validation issues found during linting.
    - Prompts the user to provide additional information based on linting problems.
    - Updates the description using the AI provider if issues are found.
    """

    fields = {"key": "AAP-lint_description_once", "description": cleaned}
    problems = validate(fields, ai_provider)[0]
    print(f"Validation issues: {problems}")

    description_problems = [p for p in problems if p.startswith("❌ Description:")]
    print(f"Description problems: {description_problems}")

    if not description_problems:
        return cleaned, False  # No issues found, no need to continue

    print("\n⚠️ Description Lint Issues:")
    for p in description_problems:
        print(f" - {p}")

    print("\n📝 Please provide more information given the problems stated above:")
    user_answers = input("> ").strip()
    print(f"User entered: {user_answers}")

    prompt = (
        "Incorporate these additional details into the below Jira description.\n"
        f"Details to incorporate: {user_answers}\n"
        "Original description:\n"
        f"{cleaned}"
    )

    # Generate the updated description
    cleaned = ai_provider.improve_text(prompt, cleaned)
    print(f"Updated cleaned description: {cleaned}")  # Debugging print

    return cleaned, True  # There are still issues, continue the loop


def lint_description(cleaned: str, ai_provider: Any) -> str:
    """
    Prints the current cleaned description in a loop for linting purposes.

    Arguments:
    - cleaned (str): The cleaned description that needs to be linted.
    - ai_provider: The AI provider used for linting.

    Side Effects:
    Prints the current cleaned description in a loop for linting purposes.
    """

    print("Starting linting...")
    while True:
        print(f"Current cleaned description: {cleaned}")  # Debugging print

        # Call the refactored function
        cleaned, should_continue = lint_description_once(cleaned, ai_provider)

        if not should_continue:
            print("No issues found, breaking out of loop.")
            break

    print("\n🤖 Final description:\n")
    print(cleaned)
    return cleaned


def update_jira_description(jira: Any, issue_key: str, cleaned: str) -> None:
    """
    Update the description of a Jira issue.

    Arguments:
    - jira: An instance of the Jira API client.
    - issue_key: A string representing the key of the Jira issue to update.
    - cleaned: A string containing the cleaned description to update the Jira issue with.

    Exceptions:
    - UpdateDescriptionError: Raised if there is an error while updating the description.

    Side Effects:
    - Modifies the description of the specified Jira issue.
    """

    try:
        print("Updating Jira description...")
        jira.update_description(issue_key, cleaned)
        print(f"✅ Updated {issue_key}")
    except UpdateDescriptionError as e:
        msg = f"❌ Update failed: {e}"
        print(msg)
        raise UpdateDescriptionError(e) from e


def cli_edit_issue(
    jira: Any, ai_provider: Any, default_prompt: str, try_cleanup_fn: Any, args: Any
) -> bool:
    """
    Edit an issue's description in a Jira instance using a command-line interface.

    Arguments:
    - jira (JIRA): A Jira instance to interact with.
    - ai_provider (AIProvider): An AI provider for natural language processing.
    - default_prompt (str): The default prompt message for user input.
    - try_cleanup_fn (function): A function to attempt cleanup operations.
    - args (Namespace): The parsed command-line arguments.

    Return:
    - bool: False if the original description is empty, indicating the issue was not edited.

    Exceptions:
    - EditIssueError: Raised if an error occurs during the editing process.
    """

    try:
        original_description = fetch_description(jira, args.issue_key)
        if not original_description:
            return False

        edited = edit_description(original_description)
        if not edited:
            return False

        prompt = get_prompt(jira, args.issue_key, default_prompt)

        cleaned = edited if args.no_ai else try_cleanup_fn(ai_provider, prompt, edited)
        if args.lint:
            cleaned = lint_description(cleaned, ai_provider)

        update_jira_description(jira, args.issue_key, cleaned)
        return True
    except EditIssueError as e:
        raise EditIssueError(e) from e
