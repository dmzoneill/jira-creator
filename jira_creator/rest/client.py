#!/usr/bin/env python
"""
A client for interacting with the Jira API, providing methods to manage issues, sprints, and user interactions.

This module defines the `JiraClient` class, which encapsulates functionality for:
- Making requests to the Jira API with proper handling of authentication and error management.
- Caching field metadata for efficient access.
- Creating, updating, and managing issues, including adding comments, changing issue types, and setting priorities.
- Retrieving information about users, issues, and sprints.
- Utility methods for debugging requests using cURL commands.

Dependencies:
- `requests`: For making HTTP requests to the Jira API.
- `core.env_fetcher`: For fetching environment variables.
- `exceptions.exceptions`: Custom exceptions for handling request errors.
- Various utility functions from the `ops` module for specific Jira operations.

Usage:
Instantiate the `JiraClient` class and use its methods to interact with Jira. Ensure that the necessary environment
variables are set for proper configuration.
"""
# pylint: disable=too-many-locals, too-many-statements, too-many-positional-arguments
# pylint: disable=too-many-public-methods, too-many-instance-attributes, too-many-arguments
# pylint: disable=import-outside-toplevel,

import json
import os
import time
import traceback
from typing import Any, Dict, Optional

import requests
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import JiraClientRequestError
from requests.exceptions import RequestException

from .ops import (  # isort: skip
    add_comment,
    add_to_sprint_by_name,
    assign_issue,
    block_issue,
    blocked,
    build_payload,
    change_issue_type,
    create_issue,
    get_acceptance_criteria,
    get_current_user,
    get_description,
    get_issue_type,
    get_user,
    list_issues,
    migrate_issue,
    remove_from_sprint,
    search_issues,
    search_users,
    set_acceptance_criteria,
    set_priority,
    set_sprint,
    set_status,
    set_story_epic,
    set_story_points,
    unassign_issue,
    unblock_issue,
    update_description,
    view_issue,
    vote_story_points,
    add_flag,
    remove_flag,
    list_sprints,
    set_summary,
    clone_issue,
    # commands entry
)


class JiraClient:
    """
    A client for interacting with the Jira API, providing methods to manage issues, projects, and various Jira
    functionalities.

    Attributes:
    - jira_url (str): The base URL for the Jira instance.
    - project_key (str): The key of the project to be managed.
    - affects_version (str): The version that the issues affect.
    - component_name (str): The name of the component related to the issues.
    - priority (str): The priority level for the issues.
    - jpat (str): The Jira Personal Access Token for authentication.
    - epic_field (str): The field used for epics in Jira.
    - board_id (str): The ID of the Jira board.
    - fields_cache_path (str): The file path for caching Jira fields.
    - is_speaking (bool): A flag indicating if the client is in speaking mode.

    Methods:
    - generate_curl_command(method, url, headers, json_data=None, params=None): Generates a curl command for debugging
    API requests.
    - cache_fields(): Caches Jira fields for efficient access, checking the cache's age.
    - get_field_name(field_id): Retrieves the name of a Jira field by its ID.
    - build_payload(summary, description, issue_type): Constructs a payload for creating or updating issues.
    - get_acceptance_criteria(issue_key): Retrieves acceptance criteria for a specified issue.
    - set_acceptance_criteria(issue_key, acceptance_criteria): Sets acceptance criteria for a specified issue.
    - get_description(issue_key): Retrieves the description of a specified issue.
    - update_description(issue_key, new_description): Updates the description of a specified issue.
    - create_issue(payload): Creates a new issue in Jira using the provided payload.
    - change_issue_type(issue_key, new_type): Changes the type of a specified issue.
    - migrate_issue(old_key, new_type): Migrates an issue to a new type.
    - add_comment(issue_key, comment): Adds a comment to a specified issue.
    - get_current_user(): Retrieves the current authenticated user.
    - get_user(str): Retrieves a user by their username or ID.
    - get_issue_type(issue_key): Retrieves the type of a specified issue.
    - unassign_issue(issue_key): Unassigns a specified issue.
    - assign_issue(issue_key, assignee): Assigns a specified issue to a user.
    - list_issues(...): Lists issues based on various optional filters.
    - set_priority(issue_key, priority): Sets the priority of a specified issue.
    - set_sprint(issue_key, sprint_id): Assigns a specified issue to a sprint.
    - remove_from_sprint(issue_key): Removes a specified issue from its sprint.
    - add_to_sprint_by_name(issue_key, sprint_name): Adds a specified issue to a sprint by its name.
    - set_status(issue_key, target_status): Sets the status of a specified issue.
    - set_story_epic(issue_key, epic_key): Assigns an epic to a specified story.
    - vote_story_points(issue_key, points): Votes on story points for a specified issue.
    - set_story_points(issue_key, points): Sets story points for a specified issue.
    - block_issue(issue_key, reason): Blocks a specified issue with a reason.
    - unblock_issue(issue_key): Unblocks a specified issue.
    - blocked(...): Lists blocked issues based on various optional filters.
    - search_issues(jql): Searches for issues using a JQL query.
    - search_users(str): Searches for users based on a string.
    - view_issue(issue_key): Retrieves details of a specified issue.
    - add_flag(issue_key): Adds a flag to a specified issue.
    - remove_flag(issue_key): Removes a flag from a specified issue.
    - list_sprints(board_id): Lists sprints for a specified board.
    - set_summary(issue_key): Sets the summary of a specified issue.
    - clone_issue(issue_key): Clones a specified issue.
    """

    def __init__(self):
        """
        Initialize a JIRA client with environment variables.

        Arguments:
        None

        Side Effects:
        - Sets instance attributes for JIRA URL, project key, affects version, component name, priority, JPAT,
        epic field, board ID, and fields cache path using environment variables fetched by EnvFetcher.
        - Sets 'is_speaking' attribute to False.
        """

        self.jira_url = EnvFetcher.get("JIRA_URL")
        self.project_key = EnvFetcher.get("PROJECT_KEY")
        self.affects_version = EnvFetcher.get("AFFECTS_VERSION")
        self.component_name = EnvFetcher.get("COMPONENT_NAME")
        self.priority = EnvFetcher.get("PRIORITY")
        self.jpat = EnvFetcher.get("JPAT")
        self.epic_field = EnvFetcher.get("JIRA_EPIC_FIELD")
        self.board_id = EnvFetcher.get("JIRA_BOARD_ID")
        self.fields_cache_path = os.path.expanduser("~/.config/rh-issue/fields.json")
        self.is_speaking = False

    def generate_curl_command(self, method, url, headers, json_data=None, params=None):
        """
        Generate a cURL command string based on the provided HTTP method, URL, headers, JSON data, and parameters.

        Arguments:
        - method (str): The HTTP method to use in the cURL command (e.g., GET, POST).
        - url (str): The URL to which the cURL command will be directed.
        - headers (Dict[str, str]): A dictionary containing the headers to include in the cURL command.
        - json_data (Optional[Dict[str, Any]]): Optional JSON data to include in the cURL command body.
        - params (Optional[Dict[str, str]]): Optional parameters to include in the cURL command.

        Side Effects:
        - Modifies the 'parts' list to build the cURL command string.

        Note: This function does not return a value.
        """
        parts = [f"curl -X {method.upper()}"]

        # Add headers
        for k, v in headers.items():
            safe_value = v
            parts.append(f"-H '{k}: {safe_value}'")

        # Add data
        if json_data:
            body = json.dumps(json_data)
            parts.append(f"--data '{body}'")

        # Add URL with query params if any
        if params:
            from urllib.parse import urlencode

            url += "?" + urlencode(params)

        parts.append(f"'{url}'")
        command = " \\\n  ".join(parts)
        command = command + "\n"

        print("\n🔧 You can debug with this curl command:\n" + command)

    def _request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> tuple:
        """
        Core request logic. Returns a tuple (status_code, result).

        Arguments:
        - method (str): The HTTP method to use for the request (e.g., 'GET', 'POST').
        - url (str): The URL to send the request to.
        - headers (Dict[str, str]): A dictionary containing the request headers.
        - json_data (Optional[Dict[str, Any]]): A dictionary containing the JSON payload for the request.
          Defaults to None.
        - params (Optional[Dict[str, str]]): A dictionary containing the query parameters for the request.
          Defaults to None.

        Return:
        - tuple: A tuple containing the HTTP status code and the parsed JSON result.

        Exceptions:
        - No exceptions are explicitly raised in this function.
        """
        try:
            response = requests.request(
                method, url, headers=headers, json=json_data, params=params, timeout=10
            )
            # Status code checks and JSON parsing
            if response.status_code == 404:
                print("❌ Resource not found")
                return response.status_code, {}

            if response.status_code == 401:
                print("❌ Unauthorized access")
                return response.status_code, {}

            if response.status_code >= 400:
                print(f"❌ Client/Server error: {response.status_code}")
                return response.status_code, {}

            if not response.content.strip():
                return response.status_code, {}  # No content, return empty dict

            try:
                result = response.json()  # Try to parse JSON
                return response.status_code, result
            except ValueError:
                print("❌ Could not parse JSON. Raw response:")
                traceback.print_exc()
                return response.status_code, {}

        except RequestException as e:
            print(f"⚠️ Request error: {e}")
            raise JiraClientRequestError(e) from e

    def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Handles retries and delegates the request to _request.

        Arguments:
        - method (str): The HTTP method to be used for the request (e.g., 'GET', 'POST').
        - path (str): The endpoint path to be appended to the base URL.
        - json_data (Optional[Dict[str, Any]]): A dictionary containing the JSON payload for the request
          (default is None).
        - params (Optional[Dict[str, str]]): A dictionary containing the query parameters for the request
          (default is None).

        Return:
        - Optional[Dict[str, Any]]: A dictionary representing the response data from the request. Returns None if there
        is no response.

        Side Effects:
        - Constructs the full URL using the base URL and the provided path.
        - Sets the necessary headers for the request, including Authorization and Content-Type.
        """

        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }

        retries = 3
        delay = 2

        for attempt in range(retries):
            status_code, result = self._request(
                method, url, headers, json_data=json_data, params=params
            )

            if 200 <= status_code < 300:  # Handle all 2xx status codes as success
                return result

            if attempt < retries - 1:
                print(f"Attempt {attempt + 1}: Sleeping before retry...")
                time.sleep(delay)
            else:
                # Generate a cURL command for debugging failed requests
                self.generate_curl_command(
                    method, url, headers, json_data=json_data, params=params
                )

                print(f"Attempt {attempt + 1}: Final failure, raising error")
                raise JiraClientRequestError(
                    f"Failed after {retries} attempts: Status Code {status_code}"
                )

        return None  # Unreachable code  # pragma: no cover

    def cache_fields(self):
        """
        Summary:
        Checks if a cache file exists and is less than 24 hours old, then loads and returns the cached data from the
        file.

        Arguments:
        - self: The instance of the class.
        (Assumed to have attributes 'fields_cache_path' specifying the path to the cache file.)

        Return:
        - The cached data loaded from the file as a Python object (e.g., dictionary, list).
        If the cache file does not exist or is older than 24 hours, the function does not return anything.
        """

        # Check if the cache file exists and is less than 24 hours old
        if os.path.exists(self.fields_cache_path):
            file_age = time.time() - os.path.getmtime(self.fields_cache_path)
            if file_age < 86400:  # 86400 seconds = 24 hours
                with open(self.fields_cache_path, "r", encoding="UTF-8") as f:
                    return json.load(f)

        # If the file doesn't exist or is older than 24 hours, update it
        fields = self.request("GET", "/rest/api/2/field")

        # Make sure the directory exists
        os.makedirs(os.path.dirname(self.fields_cache_path), exist_ok=True)

        with open(self.fields_cache_path, "w", encoding="UTF-8") as f:
            json.dump(fields, f, indent=4)

        return fields

    def get_field_name(self, field_id):
        """
        Retrieves the field name corresponding to the given field ID.

        Arguments:
        - self: The object instance.
        - field_id (int): The ID of the field for which the name is to be retrieved.

        Side Effects:
        - Updates or loads the fields from cache.
        """

        # Cache the fields (loads from cache or updates if necessary)
        fields = self.cache_fields()

        # Find the field with the matching ID
        for field in fields:
            if field["id"] == field_id:
                return field["name"]

        return None  # Return None if no field with the given ID is found

    def build_payload(self, summary, description, issue_type):
        """
        Builds a payload for creating an issue in a project with the provided summary, description, and issue type.

        Arguments:
        - summary (str): A brief summary of the issue.
        - description (str): Detailed description of the issue.
        - issue_type (str): Type of the issue.

        Return:
        The payload for creating an issue with the specified details and additional project-specific information.
        """

        return build_payload(
            summary,
            description,
            issue_type,
            self.project_key,
            self.affects_version,
            self.component_name,
            self.priority,
            self.epic_field,
        )

    def get_acceptance_criteria(self, issue_key):
        """
        Retrieves the acceptance criteria for a specific issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key identifying the specific issue for which acceptance criteria are to be retrieved.

        Return:
        - str: The acceptance criteria for the specified issue.
        """

        return get_acceptance_criteria(self.request, issue_key)

    def set_acceptance_criteria(self, issue_key, acceptance_criteria):
        """
        Sets the acceptance criteria for a specific issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key identifying the issue.
        - acceptance_criteria (str): The acceptance criteria to be set for the issue.

        Return:
        - None
        """

        return set_acceptance_criteria(self.request, issue_key, acceptance_criteria)

    def get_description(self, issue_key):
        """
        Retrieve the description of a specific issue identified by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key of the issue for which the description is requested.

        Return:
        - str: The description of the issue identified by the provided key.
        """

        return get_description(self.request, issue_key)

    def update_description(self, issue_key, new_description):
        """
        Updates the description of an issue identified by the given issue key.

        Args:
        self: The object instance.
        issue_key (str): The unique key of the issue to update.
        new_description (str): The new description to set for the issue.

        Returns:
        The result of updating the description for the specified issue.
        """

        return update_description(self.request, issue_key, new_description)

    def create_issue(self, payload):
        """
        Creates an issue using the provided payload.

        Arguments:
        - self: The object instance.
        - payload: A dictionary containing the information needed to create the issue.

        Return:
        - The result of calling the 'create_issue' function with the request and payload.
        """

        return create_issue(self.request, payload)

    def change_issue_type(self, issue_key, new_type):
        """
        Change the type of an issue in Jira.

        Arguments:
        - self: the object instance
        - issue_key (str): the key of the issue to be modified
        - new_type (str): the new type to assign to the issue

        Return:
        - The result of the change_issue_type function call with the provided parameters.
        """

        return change_issue_type(self.request, issue_key, new_type)

    def migrate_issue(self, old_key, new_type):
        """
        Migrates an issue in Jira from one type to another.

        Arguments:
        - self: The object instance.
        - old_key (str): The key of the issue to be migrated.
        - new_type (str): The new type to which the issue will be migrated.

        Return:
        - The result of migrating the issue.
        """

        return migrate_issue(
            self.request, self.jira_url, self.build_payload, old_key, new_type
        )

    def add_comment(self, issue_key, comment):
        """
        Adds a comment to an issue specified by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to add the comment to.
        - comment (str): The content of the comment to be added.

        Return:
        - The result of adding the comment to the specified issue.
        """

        return add_comment(self.request, issue_key, comment)

    def get_current_user(self):
        """
        Retrieve the current user based on the request provided.

        Arguments:
        - self: The instance of the class.
        (self) represents the instance of the class where this method is called.
        It is used to access attributes and methods within the class.

        Return:
        The current user retrieved from the request.
        The type of the returned value is dependent on the implementation of the 'get_current_user' function.
        """

        return get_current_user(self.request)

    def get_user(self, str_user):
        """
        Retrieve user information based on a provided string.

        Arguments:
        - self: The object instance.
        - str_user (str): A string used to retrieve user information.

        Return:
        - The user information retrieved based on the provided string.
        """

        return get_user(self.request, str_user)

    def get_issue_type(self, issue_key):
        """
        Retrieve the type of an issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key identifying the issue.

        Return:
        - str: The type of the issue identified by the provided key.
        """

        return get_issue_type(self.request, issue_key)

    def unassign_issue(self, issue_key):
        """
        Unassign an issue from a user.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to be unassigned.

        Return:
        - The result of unassigning the issue.
        """

        return unassign_issue(self.request, issue_key)

    def assign_issue(self, issue_key, assignee):
        """
        Assign an issue to a specific user.

        Arguments:
        - self: the object instance
        - issue_key (str): the key of the issue to be assigned
        - assignee (str): the username of the user to whom the issue will be assigned

        Return:
        - None
        """

        return assign_issue(self.request, issue_key, assignee)

    def list_issues(
        self,
        project=None,
        component=None,
        assignee=None,
        status=None,
        summary=None,
        issues_blocked=False,
        issues_unblocked=False,
        reporter=None,
    ):
        """
        Retrieve a list of issues based on specified filters such as project, component, assignee, status, summary, etc.

        Arguments:
        - project (str): The project key to filter the issues. If not provided, defaults to the project key of the
        instance.
        - component (str): The component name to filter the issues. If not provided, defaults to the component name of
        the instance.
        - assignee (str): The assignee username to filter the issues.
        - status (str): The status of the issues to filter.
        - summary (str): The summary of the issues to filter.
        - show_reason (bool): Flag to indicate whether to show reasons for the issues.
        - blocked (bool): Flag to filter blocked issues.
        - unblocked (bool): Flag to filter unblocked issues.
        - reporter (str): The reporter username to filter the issues.

        Return:
        None
        """

        component = component if component is not None else self.component_name
        project = project if project is not None else self.project_key

        return list_issues(
            self.request,
            self.get_current_user,
            project,
            component,
            assignee,
            status,
            summary,
            issues_blocked,
            issues_unblocked,
            reporter,
        )

    def set_priority(self, issue_key, priority):
        """
        Set the priority of an issue in a Jira system.

        Arguments:
        - self: the instance of the class.
        - issue_key (str): the key of the issue to set the priority for.
        - priority (str): the priority to set for the issue.

        Return:
        - None

        Exceptions:
        - None
        """

        return set_priority(self.request, issue_key, priority)

    def set_sprint(self, issue_key, sprint_id):
        """
        Set the sprint for a specific issue identified by its key.

        Arguments:
        - self: the object instance
        - issue_key (str): the key of the issue to set the sprint for
        - sprint_id (int): the ID of the sprint to set for the issue

        Return:
        - None
        """

        return set_sprint(self.request, issue_key, sprint_id)

    def remove_from_sprint(self, issue_key):
        """
        Remove an issue from the current sprint.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key identifying the issue to be removed from the sprint.

        Return:
        - None
        """

        return remove_from_sprint(self.request, issue_key)

    def add_to_sprint_by_name(self, issue_key, sprint_name):
        """
        Adds an issue to a sprint on a board by name.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to be added to the sprint.
        - sprint_name (str): The name of the sprint to which the issue will be added.

        Return:
        - None
        """

        return add_to_sprint_by_name(
            self.request, self.board_id, issue_key, sprint_name
        )

    def set_status(self, issue_key, target_status):
        """
        Set the status of an issue identified by its key to a target status.

        Arguments:
        - self: the object instance
        - issue_key (str): the key identifying the issue
        - target_status (str): the status to set the issue to

        Return:
        - None

        Exceptions:
        - None
        """

        return set_status(self.request, issue_key, target_status)

    def set_story_epic(self, issue_key, epic_key):
        """
        Sets the epic link for a given story in Jira.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the story issue to set the epic link for.
        - epic_key (str): The key of the epic to link the story to.

        Return:
        - None
        """

        return set_story_epic(self.request, issue_key, epic_key)

    def vote_story_points(self, issue_key, points):
        """
        Cast a vote for story points on a specific issue.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to vote on.
        - points (int): The number of story points to vote for the issue.

        Return:
        - None
        """

        return vote_story_points(self.request, issue_key, points)

    def set_story_points(self, issue_key, points):
        """
        Set the story points for a specific issue identified by the given key.

        Arguments:
        - self: the object instance
        - issue_key (str): the key identifying the specific issue
        - points (int): the number of story points to set for the issue

        Return:
        - None
        """

        return set_story_points(self.request, issue_key, points)

    def block_issue(self, issue_key, reason):
        """
        Blocks an issue by providing a reason for blocking.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key identifying the issue to be blocked.
        - reason (str): The reason for blocking the issue.

        Return:
        - None
        """

        return block_issue(self.request, issue_key, reason)

    def unblock_issue(self, issue_key):
        """
        Unblocks an issue by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key identifying the issue to unblock.

        Return:
        - The result of unblocking the issue.
        """

        return unblock_issue(self.request, issue_key)

    def blocked(self, project=None, component=None, assignee=None):
        """
        Calls the 'blocked' function with parameters related to project, component, and assignee.

        Arguments:
        - project (str): The project name to filter the issues.
        - component (str): The component name to filter the issues.
        - assignee (str): The assignee name to filter the issues.

        Returns:
        - The result of the 'blocked' function with the provided parameters.
        """

        return blocked(self.list_issues, project, component, assignee)

    def search_issues(self, jql):
        """
        Search for issues in Jira based on a JQL query.

        Arguments:
        - self: the object instance
        - jql (str): the JQL query string used to search for issues in Jira

        Return:
        - The result of the search_issues function, which is not specified in the provided code.
        """

        return search_issues(self.request, jql)

    def search_users(self, str_user):
        """
        Search for users based on a given string.

        Arguments:
        - self: the object instance
        - str_user (str): the string used to search for users

        Return:
        - The result of the search_users method called with the request attribute and the provided string.
        """

        return search_users(self.request, str_user)

    def view_issue(self, issue_key):
        """
        View an issue by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to view.

        Return:
        - The result of viewing the issue.
        """

        return view_issue(self.request, issue_key)

    def add_flag(self, issue_key):
        """
        Adds a flag to an issue identified by the provided issue key.

        Args:
        self: The object instance.
        issue_key (str): The key identifying the issue to which the flag will be added.

        Returns:
        The result of adding a flag to the specified issue.
        """

        return add_flag(self.request, issue_key)

    def remove_flag(self, issue_key):
        """
        Remove a flag from an issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key identifying the issue from which the flag will be removed.

        Return:
        - None
        """

        return remove_flag(self.request, issue_key)

    def list_sprints(self, board_id):
        """
        Retrieve a list of sprints associated with a specific board.

        Arguments:
        - self: The object instance.
        - board_id (int): The unique identifier of the board for which to fetch the list of sprints.

        Return:
        List: A list of sprints associated with the specified board.
        """

        return list_sprints(self.request, board_id)

    def set_summary(self, issue_key, summary):
        """
        Sets the summary of an issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key that identifies the issue for which the summary needs to be set.
        - summary (str): The new summary.

        Returns:
        - None
        """

        return set_summary(self.request, issue_key, summary)

    def clone_issue(self, issue_key):
        """
        Clones an issue in the system identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key identifying the issue to be cloned.

        Return:
        - The result of cloning the issue.
        """

        return clone_issue(self.request, issue_key)
