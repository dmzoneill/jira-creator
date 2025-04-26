#!/usr/bin/env python
"""
This module provides functionality for validating Jira issues based on various criteria, leveraging AI for quality
checks on specific fields.

Key components of the module include:

- **Functions for Cache Management**:
- `get_cache_path()`: Returns the path to the cache file for storing issue hashes.
- `load_cache()`: Loads cached issue data from the cache file, if it exists.
- `save_cache(data)`: Saves the provided data to the cache file, creating necessary directories if they do not exist.
- `load_and_cache_issue(issue_key)`: Loads the cache and retrieves cached values for a specified issue key.

- **Validation Functions**:
- A series of functions that validate various aspects of a Jira issue, including:
- `validate_progress()`: Checks if the issue is assigned when in progress.
- `validate_epic_link()`: Ensures an issue has an assigned epic link.
- `validate_sprint()`: Validates that the issue is assigned to a sprint when in progress.
- `validate_priority()`: Confirms that the priority is set.
- `validate_story_points()`: Checks if story points are assigned, based on the issue's status.
- `validate_blocked()`: Validates that blocked issues have a reason.
- `validate_field_with_ai()`: Uses an AI provider to validate field quality.

- **Main Validation Function**:
- `cli_validate_issue(fields, ai_provider)`: Orchestrates the validation of an issue by extracting relevant fields,
performing validations, and utilizing AI for quality checks.

This module is intended for use in a command-line interface context, providing feedback on issues that do not meet the
specified validation rules.
"""

# pylint: disable=too-many-locals too-many-arguments too-many-positional-arguments

import hashlib
import json
import os
from typing import Any, Dict, List, Tuple

from core.env_fetcher import EnvFetcher
from providers.ai_provider import AIProvider


def get_cache_path() -> str:
    """
    Return the path to the cache file for storing AI hashes.

    Returns:
    str: A string representing the file path to the cache file for AI hashes.
    """
    return os.path.expanduser("~/.config/rh-issue/ai-hashes.json")


def sha256(text: str) -> str:
    """
    Return the SHA-256 hash of the input text.

    Arguments:
    - text (str): The text to be hashed using the SHA-256 algorithm.

    Return:
    - str: The hexadecimal representation of the SHA-256 hash of the input text.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cache() -> Dict[str, Any]:
    """
    Load cached data from a file if it exists, otherwise return an empty dictionary.

    Return:
    dict: A dictionary containing the cached data if the cache file exists, otherwise an empty dictionary.
    """
    if os.path.exists(get_cache_path()):
        with open(get_cache_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(data: Dict[str, Any]) -> None:
    """
    Save_cache function retrieves the directory path for the cache and stores it in the cache_dir variable.

    Arguments:
    - data: The data to be cached.

    Return:
    This function does not return anything.
    """
    cache_dir = os.path.dirname(get_cache_path())

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)  # Ensure directory exists

    with open(get_cache_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_and_cache_issue(issue_key: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load cache and get the cached values for a given issue key.

    Arguments:
    - issue_key (str): A string representing the key of the issue for which cached values are retrieved.

    Return:
    - tuple: A tuple containing the cache (dict) and the cached values for the specified issue key (dict).
    """
    cache = load_cache()
    cached = cache.get(issue_key, {})
    return cache, cached


def validate_progress(
    status: str, assignee: str, problems: List[str], issue_status: Dict[str, bool]
) -> None:
    """
    Validate if the issue is assigned when it's in progress.

    Arguments:
    - status (str): The status of the issue.
    - assignee (str): The person assigned to the issue.
    - problems (list): A list to store validation problems.
    - issue_status (dict): A dictionary to track the status of the issue.
    """
    if status == "In Progress" and not assignee:
        problems.append("❌ Issue is In Progress but unassigned")
        issue_status["Progress"] = False
    else:
        issue_status["Progress"] = True


def validate_epic_link(
    issue_type: str,
    status: str,
    epic_link: str,
    problems: List[str],
    issue_status: Dict[str, bool],
) -> None:
    """
    Validate if an issue has an assigned epic link.

    Arguments:
    - issue_type (str): The type of the issue (e.g., "Bug", "Story", "Epic").
    - status (str): The status of the issue.
    - epic_link (str): The epic link assigned to the issue.
    - problems (list): A list to store validation problems.
    - issue_status (dict): A dictionary to track the status of different aspects of the issue.
    """
    epic_exempt_types = ["Epic"]
    epic_exempt_statuses = ["New", "Refinement"]
    if (
        issue_type not in epic_exempt_types
        and not (
            issue_type in ["Bug", "Story", "Spike", "Task"]
            and status in epic_exempt_statuses
        )
        and not epic_link
    ):
        problems.append("❌ Issue has no assigned Epic")
        issue_status["Epic"] = False
    else:
        issue_status["Epic"] = True


def validate_sprint(
    status: str, sprint_field: bool, problems: List[str], issue_status: Dict[str, bool]
) -> None:
    """
    Validate if the issue is assigned to a sprint when in progress.

    Arguments:
    - status (str): The status of the issue.
    - sprint_field (bool): Indicates if the issue is assigned to a sprint.
    - problems (list): A list to store validation problems.
    - issue_status (dict): A dictionary to track the issue status.
    """
    if status == "In Progress" and not sprint_field:
        problems.append("❌ Issue is In Progress but not assigned to a Sprint")
        issue_status["Sprint"] = False
    else:
        issue_status["Sprint"] = True


def validate_priority(
    priority: bool, problems: List[str], issue_status: Dict[str, bool]
) -> None:
    """
    Validate if priority is set.

    Arguments:
    - priority (bool): Represents whether priority is set or not.
    - problems (list): A list to store validation problems.
    - issue_status (dict): A dictionary to track the status of different fields.
    """
    if not priority:
        problems.append("❌ Priority not set")
        issue_status["Priority"] = False
    else:
        issue_status["Priority"] = True


def validate_story_points(
    story_points: int, status: str, problems: List[str], issue_status: Dict[str, bool]
) -> None:
    """
    Validate if story points are assigned, unless the status is 'Refinement' or 'New'.

    Arguments:
    - story_points (int): The number of story points assigned to a task.
    - status (str): The current status of the task.
    - problems (list): A list to store validation problems.
    - issue_status (dict): A dictionary to track the status of different issues.
    """
    if story_points is None and status not in ["Refinement", "New"]:
        problems.append("❌ Story points not assigned")
        issue_status["Story P."] = False
    else:
        issue_status["Story P."] = True


def validate_blocked(
    blocked_value: str,
    blocked_reason: str,
    problems: List[str],
    issue_status: Dict[str, bool],
) -> None:
    """
    Validate if blocked issues have a reason.

    Arguments:
    - blocked_value (str): A string indicating if the issue is blocked.
    - blocked_reason (str): The reason for blocking the issue.
    - problems (list): A list to store validation problems.
    - issue_status (dict): A dictionary containing the status of the issue.
    """
    if blocked_value == "True" and not blocked_reason:
        problems.append("❌ Issue is blocked but has no blocked reason")
        issue_status["Blocked"] = False
    else:
        issue_status["Blocked"] = True


def validate_field_with_ai(
    field_name: str,
    field_value: str,
    field_hash: str,
    cached_field_hash: str,
    ai_provider: AIProvider,
    problems: List[str],
    issue_status: Dict[str, bool],
) -> str:
    """
    Validate a field using an AI provider by comparing field hashes and checking the quality of the field value.

    Arguments:
    - field_name (str): The name of the field being validated.
    - field_value (str): The value of the field being validated.
    - field_hash (str): The hash of the current field value.
    - cached_field_hash (str): The cached hash of the field value.
    - ai_provider (object): The AI provider object used to improve text quality.
    - problems (list): A list to store validation problems encountered.
    - issue_status (dict): A dictionary to track the validation status of each field.

    Return:
    - str: The updated cached field hash to use in the next validation.
    """
    if field_value:
        # Ensure the field hash comparison is correct
        if field_hash != cached_field_hash:
            reviewed = ai_provider.improve_text(
                f"""Check the quality of the following Jira {field_name}.
                Is it clear, concise, and informative? Respond with 'OK' if fine or explain why not.""",
                field_value,
            )
            if "ok" not in reviewed.lower():  # If AI response is not OK
                problems.append(f"❌ {field_name}: {reviewed.strip()}")
                issue_status[field_name] = False
            else:
                cached_field_hash = field_hash  # Update the cached hash here
                issue_status[field_name] = True
        elif field_hash == cached_field_hash and "ok" not in field_value.lower():
            problems.append(f"❌ {field_name}: {field_value.strip()}")
            issue_status[field_name] = False

    return cached_field_hash  # Return the updated hash to use in the next validation


def cli_validate_issue(
    fields: Dict[str, Any], ai_provider: AIProvider
) -> Tuple[List[str], Dict[str, bool]]:
    """
    Validate the fields of an issue using an AI provider to ensure compliance with specified criteria.

    Arguments:
    - fields (Dict[str, Any]): A dictionary containing the fields of the issue to be validated.
    - ai_provider (AIProvider): The AI provider used for validation.

    Return:
    - Tuple[List[str], Dict[str, bool]]: A tuple containing:
    - problems (List[str]): A list of validation issues encountered during the process.
    - issue_status (Dict[str, bool]): A dictionary tracking the validation status of each field.
    """
    problems: List[str] = []
    issue_status: Dict[str, bool] = {}

    # Extract and validate basic fields
    issue_key = fields.get("key")
    if not issue_key:
        return problems, issue_status

    status = fields.get("status", {}).get("name")
    assignee = fields.get("assignee")
    epic_link = fields.get(EnvFetcher.get("JIRA_EPIC_FIELD"))
    sprint_field = fields.get(EnvFetcher.get("JIRA_SPRINT_FIELD"))
    priority = fields.get("priority")
    story_points = fields.get(EnvFetcher.get("JIRA_STORY_POINTS_FIELD"))
    blocked_value = fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value")
    blocked_reason = fields.get(EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"))

    # Load cache for the issue
    cache, cached = load_and_cache_issue(issue_key)

    # Validate various fields
    validate_progress(status, assignee, problems, issue_status)
    validate_epic_link(
        fields.get("issuetype", {}).get("name"),
        status,
        epic_link,
        problems,
        issue_status,
    )
    validate_sprint(status, sprint_field, problems, issue_status)
    validate_priority(priority, problems, issue_status)
    validate_story_points(story_points, status, problems, issue_status)
    validate_blocked(blocked_value, blocked_reason, problems, issue_status)

    # Validate summary, description, and acceptance criteria using AI
    summary = fields.get("summary", "")
    summary_hash = sha256(summary) if summary else None
    cached["summary_hash"] = validate_field_with_ai(
        "Summary",
        summary,
        summary_hash,
        cached.get("summary_hash", ""),
        ai_provider,
        problems,
        issue_status,
    )

    description = fields.get("description", "")
    description_hash = sha256(description) if description else None
    cached["description_hash"] = validate_field_with_ai(
        "Description",
        description,
        description_hash,
        cached.get("description_hash", ""),
        ai_provider,
        problems,
        issue_status,
    )

    acceptance_criteria = fields.get(
        EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"), ""
    )
    acceptance_criteria_hash = (
        sha256(acceptance_criteria) if acceptance_criteria else None
    )
    cached["acceptance_criteria_hash"] = validate_field_with_ai(
        "Acceptance Criteria",
        acceptance_criteria,
        acceptance_criteria_hash,
        cached.get("acceptance_criteria_hash", ""),
        ai_provider,
        problems,
        issue_status,
    )

    # Save the updated cache
    cache[issue_key] = cached
    save_cache(cache)

    return problems, issue_status
