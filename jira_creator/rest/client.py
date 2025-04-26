#!/usr/bin/env python
"""
This module defines the JiraClient class, which provides a comprehensive interface for interacting with the Jira API.
It facilitates various operations related to Jira issues, sprints, and users, enabling seamless management of Jira
resources through a programmatic approach.

Key Features:
- Issue Management: Create, update, assign, and comment on issues, as well as manage issue types and priorities.
- Sprint Management: Add or remove issues from sprints, list sprints, and set sprint details.
- User Management: Retrieve current user details and search for users within Jira.
- Error Handling: Robust error handling for request failures, with support for generating debug-friendly curl commands
for troubleshooting.

The JiraClient class relies on environment variables for configuration and uses the requests library for making HTTP
requests. Additionally, it incorporates custom modules for enhanced environment management and exception handling.

Dependencies:
- requests: For HTTP communication with the Jira API.
- Custom modules: For environment variable fetching and exception management.

The module is designed to be easily integrated into larger systems requiring Jira API interactions, providing a
high-level abstraction over the API's complexity while maintaining flexibility and ease of use.
"""

# pylint: disable=too-many-instance-attributes too-many-arguments too-many-positional-arguments
# pylint: disable=import-outside-toplevel too-many-public-methods
# /* jscpd:ignore-start */

import json
import os
import time
import traceback
from typing import Any, Dict, Optional, Tuple

import requests
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import JiraClientRequestError
from requests.exceptions import RequestException

from .ops import (  # isort: skip
    add_comment,
    add_to_sprint,
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
    get_sprint,
)


class JiraClient:
    """
    A client for interacting with the Jira API, providing methods to manage issues, fields, and other Jira
    functionalities.

    Attributes:
    jira_url (str): The base URL for the Jira instance.
    project_key (str): The key of the project to which issues belong.
    affects_version (str): The version that issues affect.
    component_name (str): The name of the component related to issues.
    priority (str): The priority level for issues.
    jpat (str): The Jira personal access token for authentication.
    epic_field (str): The field used to identify epics in Jira.
    board_id (str): The ID of the Jira board.
    fields_cache_path (str): The file path for caching Jira fields.
    is_speaking (bool): A flag indicating whether the client is in speaking mode.

    Methods:
    generate_curl_command: Constructs and prints a curl command for debugging API requests.
    request: Makes an HTTP request to the Jira API and handles retries.
    cache_fields: Caches Jira fields for quicker access.
    get_field_name: Retrieves the name of a field by its ID.
    build_payload: Creates a payload for issue creation with specified details.
    get_acceptance_criteria: Fetches acceptance criteria for a given issue.
    set_acceptance_criteria: Updates the acceptance criteria for a specified issue.
    get_description: Retrieves the description of an issue.
    update_description: Updates the description of an issue.
    create_issue: Creates a new issue in Jira.
    change_issue_type: Changes the type of an existing issue.
    migrate_issue: Migrates an issue to a new type.
    add_comment: Adds a comment to a specified issue.
    get_current_user: Retrieves the currently authenticated user.
    get_user: Fetches user information based on a username.
    get_issue_type: Gets the issue type for a specified issue.
    unassign_issue: Unassigns an issue from its current assignee.
    assign_issue: Assigns an issue to a specified user.
    list_issues: Lists issues based on various filtering criteria.
    set_priority: Sets the priority of a specified issue.
    set_sprint: Assigns a sprint to an issue.
    remove_from_sprint: Removes an issue from its current sprint.
    add_to_sprint: Adds an issue to a specified sprint.
    set_status: Updates the status of an issue.
    set_story_epic: Associates a story with an epic.
    vote_story_points: Votes on story points for an issue.
    set_story_points: Sets story points for an issue.
    block_issue: Blocks an issue with a specified reason.
    unblock_issue: Unblocks a previously blocked issue.
    blocked: Retrieves issues that are currently blocked.
    search_issues: Searches for issues using JQL.
    search_users: Searches for users based on a username.
    view_issue: Retrieves detailed information about a specific issue.
    add_flag: Adds a flag to an issue.
    remove_flag: Removes a flag from an issue.
    list_sprints: Lists sprints for a specified board.
    set_summary: Updates the summary of an issue.
    clone_issue: Clones an existing issue.
    get_sprint: Retrieves information about the current sprint.
    """

    def __init__(self) -> None:
        """
        Initialize the configuration settings for JIRA integration.

        Arguments:
        - None

        Side Effects:
        - Sets up various configuration parameters for JIRA integration using environment variables fetched by
        EnvFetcher.
        - Initializes attributes for JIRA URL, project key, affects version, component name, priority, JIRA PAT, epic
        field, board ID, fields cache path, and speaking status.
        """
        self.jira_url: str = EnvFetcher.get("JIRA_URL")
        self.project_key: str = EnvFetcher.get("PROJECT_KEY")
        self.affects_version: str = EnvFetcher.get("AFFECTS_VERSION")
        self.component_name: str = EnvFetcher.get("COMPONENT_NAME")
        self.priority: str = EnvFetcher.get("PRIORITY")
        self.jpat: str = EnvFetcher.get("JPAT")
        self.epic_field: str = EnvFetcher.get("JIRA_EPIC_FIELD")
        self.board_id: str = EnvFetcher.get("JIRA_BOARD_ID")
        self.fields_cache_path: str = os.path.expanduser(
            "~/.config/rh-issue/fields.json"
        )
        self.is_speaking: bool = False

    def generate_curl_command(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Generate a curl command for debugging HTTP requests.

        Arguments:
        - method (str): The HTTP method to use (e.g., GET, POST).
        - url (str): The URL to send the request to.
        - headers (Dict[str, str]): A dictionary containing the request headers.
        - json_data (Optional[Dict[str, Any]]): Optional JSON data to include in the request body.
        - params (Optional[Dict[str, str]]): Optional query parameters to append to the URL.

        Side Effects:
        - Prints the generated curl command for debugging purposes.
        """
        parts = [f"curl -X {method.upper()}"]

        for k, v in headers.items():
            safe_value = v
            parts.append(f"-H '{k}: {safe_value}'")

        if json_data:
            body = json.dumps(json_data)
            parts.append(f"--data '{body}'")

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
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Send a request to a specified URL using the provided method, headers, JSON data, and parameters.

        Arguments:
        - method (str): The HTTP method to use for the request (e.g., 'GET', 'POST').
        - url (str): The URL to send the request to.
        - headers (Dict[str, str]): A dictionary containing the request headers.
        - json_data (Optional[Dict[str, Any]]): Optional JSON data to send with the request. Defaults to None.
        - params (Optional[Dict[str, str]]): Optional query parameters to include in the request URL. Defaults to None.

        Returns:
        Tuple[int, Dict[str, Any]]: A tuple containing the HTTP status code of the response and a dictionary
        representing the response data.

        Exceptions:
        - JiraClientRequestError: Raised when an error occurs during the request.

        Side Effects:
        - Prints error messages if the response status code indicates a client/server error, unauthorized access, or if
        JSON parsing fails.
        - Raises an exception if a RequestException occurs during the request.
        """
        try:
            response = requests.request(
                method, url, headers=headers, json=json_data, params=params, timeout=10
            )
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
                return response.status_code, {}

            try:
                result = response.json()
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
        Performs a HTTP request to a Jira server using the provided method, path, JSON data, and parameters.

        Arguments:
        - method (str): The HTTP method to use for the request (e.g., 'GET', 'POST').
        - path (str): The endpoint path to append to the Jira server URL.
        - json_data (Optional[Dict[str, Any]]): JSON data to be included in the request body (default is None).
        - params (Optional[Dict[str, str]]): Query parameters to include in the request URL (default is None).

        Returns:
        - Optional[Dict[str, Any]]: A dictionary containing the response data if the request is successful. Returns
        None if all retry attempts fail.

        Exceptions:
        - JiraClientRequestError: Raised if the request fails after all retry attempts.

        Side Effects:
        - May print debug information during retry attempts.
        - May make multiple HTTP requests in case of failures.
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

            if 200 <= status_code < 300:
                return result

            if attempt < retries - 1:
                print(f"Attempt {attempt + 1}: Sleeping before retry...")
                time.sleep(delay)

        self.generate_curl_command(
            method, url, headers, json_data=json_data, params=params
        )
        print(f"Attempt {attempt + 1}: Final failure, raising error")
        raise JiraClientRequestError(
            f"Failed after {retries} attempts: Status Code {status_code}"
        )

    def cache_fields(self) -> Optional[Dict[str, Any]]:
        """
        Cache the fields data either by loading from a cache file or fetching from the server and saving to the cache
        file.

        Arguments:
        - self: The instance of the class.

        Return:
        - Optional[Dict[str, Any]]: A dictionary containing the fields data, or None if the data could not be retrieved.

        Exceptions:
        - None
        """
        if os.path.exists(self.fields_cache_path):
            file_age = time.time() - os.path.getmtime(self.fields_cache_path)
            if file_age < 86400:
                with open(self.fields_cache_path, "r", encoding="UTF-8") as f:
                    return json.load(f)

        fields = self.request("GET", "/rest/api/2/field")

        os.makedirs(os.path.dirname(self.fields_cache_path), exist_ok=True)

        with open(self.fields_cache_path, "w", encoding="UTF-8") as f:
            json.dump(fields, f, indent=4)

        return fields

    def get_field_name(self, field_id: str) -> Optional[str]:
        """
        Returns the name of a field based on its ID.

        Arguments:
        - field_id (str): The ID of the field to retrieve its name.

        Return:
        - Optional[str]: The name of the field corresponding to the provided ID. Returns None if the field ID is not
        found.
        """
        fields = self.cache_fields()

        for field in fields:
            if field["id"] == field_id:
                return field["name"]

        return None

    def build_payload(
        self, summary: str, description: str, issue_type: str
    ) -> Dict[str, Any]:
        """
        Builds a payload for an issue creation request in a project management system.

        Arguments:
        - summary (str): A brief summary or title of the issue.
        - description (str): Detailed description of the issue.
        - issue_type (str): Type of the issue (e.g., bug, task, story).

        Return:
        - Dict[str, Any]: A dictionary representing the payload for the issue creation request.
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

    def get_acceptance_criteria(self, issue_key: str) -> str:
        """
        Retrieve acceptance criteria for a specific Jira issue.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The key of the Jira issue for which acceptance criteria are requested.

        Return:
        - str: The acceptance criteria associated with the provided Jira issue key.
        """
        return get_acceptance_criteria(self.request, issue_key)

    def set_acceptance_criteria(self, issue_key: str, acceptance_criteria: str) -> None:
        """
        Sets the acceptance criteria for a specific issue identified by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue for which acceptance criteria will be set.
        - acceptance_criteria (str): The acceptance criteria to be set for the issue.

        Side Effects:
        Modifies the acceptance criteria for the specified issue.
        """
        return set_acceptance_criteria(self.request, issue_key, acceptance_criteria)

    def get_description(self, issue_key: str) -> str:
        """
        Retrieve the description of a specific issue identified by the given issue key.

        Arguments:
        - self: The object instance
        - issue_key (str): A string representing the unique key of the issue

        Return:
        - str: The description of the issue identified by the provided issue key
        """
        return get_description(self.request, issue_key)

    def update_description(self, issue_key: str, new_description: str) -> None:
        """
        Updates the description of an issue identified by the given issue key.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The key identifying the issue to update.
        - new_description (str): The new description to set for the issue.

        Side Effects:
        - Modifies the description of the specified issue.
        """
        return update_description(self.request, issue_key, new_description)

    def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an issue using the provided payload data.

        Arguments:
        - self: The instance of the class.
        - payload (Dict[str, Any]): A dictionary containing data to create the issue.

        Return:
        - Dict[str, Any]: A dictionary representing the created issue.
        """
        return create_issue(self.request, payload)

    def change_issue_type(self, issue_key: str, new_type: str) -> None:
        """
        Change the type of an issue in a system.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key identifying the issue to be modified.
        - new_type (str): The new type to assign to the issue.

        Side Effects:
        - Modifies the type of the specified issue.
        """
        return change_issue_type(self.request, issue_key, new_type)

    def migrate_issue(self, old_key: str, new_type: str) -> None:
        """
        Migrate an issue in Jira from one type to another using the provided old key and new type.

        Arguments:
        - old_key (str): The old key of the issue to migrate.
        - new_type (str): The new type to migrate the issue to.

        Side Effects:
        - Modifies the issue type of the specified Jira issue.
        """
        return migrate_issue(
            self.request, self.jira_url, self.build_payload, old_key, new_type
        )

    def add_comment(self, issue_key: str, comment: str) -> None:
        """
        Adds a comment to an issue specified by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to add the comment to.
        - comment (str): The content of the comment to be added.

        Exceptions:
        - None
        """
        return add_comment(self.request, issue_key, comment)

    def get_current_user(self) -> Any:
        """
        Get the current user.

        Arguments:
        - self: The instance of the class.
        It is used to access the instance attributes and methods.

        Return:
        - Any: The current user object retrieved from the request.
        """
        return get_current_user(self.request)

    def get_user(self, str_user: str) -> Any:
        """
        Retrieve a user based on the provided username.

        Arguments:
        - self: The instance of the class.
        - str_user (str): The username of the user to retrieve.

        Return:
        - Any: The user object corresponding to the provided username.
        """
        return get_user(self.request, str_user)

    def get_issue_type(self, issue_key: str) -> str:
        """
        Get the type of an issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): A string representing the unique key of the issue.

        Return:
        - str: The type of the issue identified by the provided issue key.
        """
        return get_issue_type(self.request, issue_key)

    def unassign_issue(self, issue_key: str) -> None:
        """
        Unassign an issue from a user.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The key of the issue to be unassigned.

        Side Effects:
        - This function interacts with an external service to unassign the specified issue.
        """
        return unassign_issue(self.request, issue_key)

    def assign_issue(self, issue_key: str, assignee: str) -> None:
        """
        Assign an issue to a specific assignee.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to be assigned.
        - assignee (str): The username of the user to whom the issue will be assigned.

        Side Effects:
        - Modifies the assignment of the specified issue to the provided assignee.
        """
        return assign_issue(self.request, issue_key, assignee)

    def list_issues(
        self,
        project: Optional[str] = None,
        component: Optional[str] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
        summary: Optional[str] = None,
        issues_blocked: bool = False,
        issues_unblocked: bool = False,
        reporter: Optional[str] = None,
    ) -> None:
        """
        Retrieve a list of issues based on specified filters.

        Arguments:
        - project (Optional[str]): The project key to filter the issues. If None, the default project key from the
        class instance will be used.
        - component (Optional[str]): The component name to filter the issues. If None, the default component name from
        the class instance will be used.
        - assignee (Optional[str]): The assignee to filter the issues.
        - status (Optional[str]): The status to filter the issues.
        - summary (Optional[str]): The summary to filter the issues.
        - issues_blocked (bool): Flag to indicate whether to include blocked issues.
        - issues_unblocked (bool): Flag to indicate whether to include unblocked issues.
        - reporter (Optional[str]): The reporter to filter the issues.

        Returns:
        - None

        Side Effects:
        - Calls the 'list_issues' function with specified parameters to retrieve a list of filtered issues.
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

    def set_priority(self, issue_key: str, priority: str) -> None:
        """
        Sets the priority of an issue identified by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key of the issue.
        - priority (str): The new priority to set for the issue.

        Side Effects:
        Modifies the priority of the specified issue.
        """
        return set_priority(self.request, issue_key, priority)

    def set_sprint(self, issue_key: str, sprint_id: int) -> None:
        """
        Set the sprint for a specific issue identified by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue to set the sprint for.
        - sprint_id (int): The ID of the sprint to set for the issue.

        This function sets the sprint for the specified issue using the provided issue key and sprint ID.
        """
        return set_sprint(self.request, issue_key, sprint_id)

    def remove_from_sprint(self, issue_key: str) -> None:
        """
        Remove an issue from the current sprint.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The key of the issue to be removed from the sprint.

        Side Effects:
        - Modifies the sprint by removing the specified issue.
        """
        return remove_from_sprint(self.request, issue_key)

    def add_to_sprint(self, issue_key: str, sprint_name: str, assignee: str) -> None:
        """
        Add an issue to a sprint on a board.

        Arguments:
        - issue_key (str): The key of the issue to be added to the sprint.
        - sprint_name (str): The name of the sprint to add the issue to.

        Side Effects:
        Modifies the sprint by adding the specified issue to it.
        """
        return add_to_sprint(
            self.request, self.board_id, issue_key, sprint_name, assignee
        )

    def set_status(self, issue_key: str, target_status: str) -> None:
        """
        Sets the status of an issue specified by the issue key to the target status.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The unique key identifying the issue.
        - target_status (str): The desired status to set for the issue.

        Exceptions:
        This function does not raise any exceptions.

        Side Effects:
        Modifies the status of the specified issue.
        """
        return set_status(self.request, issue_key, target_status)

    def set_story_epic(self, issue_key: str, epic_key: str) -> None:
        """
        Sets the epic link for a given story in Jira.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the story/issue to update.
        - epic_key (str): The key of the epic to link the story to.

        No return value.
        """
        return set_story_epic(self.request, issue_key, epic_key)

    def vote_story_points(self, issue_key: str, points: int) -> None:
        """
        Vote on the story points for a specific issue.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the Jira issue on which to vote for story points.
        - points (int): The number of story points to vote for the issue.

        Side Effects:
        - Modifies the story points for the specified Jira issue.

        Note:
        - This function internally calls another function 'vote_story_points' passing 'self.request', issue_key, and
        points as arguments.
        """
        return vote_story_points(self.request, issue_key, points)

    def set_story_points(self, issue_key: str, points: int) -> None:
        """
        Sets the story points for a specific issue identified by its key.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The unique key identifying the issue.
        - points (int): The story points to be set for the issue.

        Exceptions:
        None
        """
        return set_story_points(self.request, issue_key, points)

    def block_issue(self, issue_key: str, reason: str) -> None:
        """
        Blocks an issue by providing a reason for blocking.

        Arguments:
        - issue_key (str): The key identifying the issue to be blocked.
        - reason (str): The reason for blocking the issue.

        Side Effects:
        Modifies the state by blocking the specified issue with the given reason.
        """
        return block_issue(self.request, issue_key, reason)

    def unblock_issue(self, issue_key: str) -> None:
        """
        Unblocks an issue by sending a request with the given issue key.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The key of the issue to unblock.

        Side Effects:
        - Sends a request to unblock the specified issue using the provided issue key.
        """
        return unblock_issue(self.request, issue_key)

    def blocked(
        self,
        project: Optional[str] = None,
        component: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Any:
        """
        Retrieves a list of blocked issues based on the specified project, component, and assignee.

        Arguments:
        - project (Optional[str]): The name of the project to filter the blocked issues. Default is None.
        - component (Optional[str]): The name of the component to filter the blocked issues. Default is None.
        - assignee (Optional[str]): The name of the assignee to filter the blocked issues. Default is None.

        Return:
        - Any: A list of blocked issues based on the provided project, component, and assignee.
        """
        return blocked(self.list_issues, project, component, assignee)

    def search_issues(self, jql: str) -> Any:
        """
        Search for issues in Jira based on the provided JQL query.

        Arguments:
        - jql (str): The Jira Query Language (JQL) query used to search for issues.

        Return:
        - Any: The result of the search_issues function with the provided request and JQL query.
        """
        return search_issues(self.request, jql)

    def search_users(self, str_user: str) -> Any:
        """
        Search for users based on a given string.

        Arguments:
        - self: The object instance.
        - str_user (str): The string used to search for users.

        Return:
        - Any: The result of searching for users based on the provided string.
        """
        return search_users(self.request, str_user)

    def view_issue(self, issue_key: str) -> Any:
        """
        View an issue by its key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key identifying the issue to view.

        Return:
        - Any: The result of viewing the issue.
        """
        return view_issue(self.request, issue_key)

    def add_flag(self, issue_key: str) -> None:
        """
        Adds a flag to a specified issue identified by the issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key identifying the issue to which the flag will be added.

        Exceptions:
        None
        """
        return add_flag(self.request, issue_key)

    def remove_flag(self, issue_key: str) -> None:
        """
        Removes a flag associated with a specific issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The key of the issue from which the flag will be removed.

        Side Effects:
        - Modifies the state by removing a flag associated with the provided issue key.
        """
        return remove_flag(self.request, issue_key)

    def list_sprints(self, board_id: int) -> Any:
        """
        Retrieves a list of sprints associated with a specific board.

        Arguments:
        - board_id (int): The unique identifier of the board for which to retrieve sprints.

        Return:
        - Any: A list of sprints associated with the specified board.
        """
        return list_sprints(self.request, board_id)

    def set_summary(self, issue_key: str, summary: str) -> None:
        """
        Set the summary of an issue identified by the given issue key.

        Arguments:
        - self: The object instance.
        - issue_key (str): The unique key identifying the issue.
        - summary (str): The new summary to set for the issue.

        Side Effects:
        - Modifies the summary of the issue identified by the provided issue key.
        """
        return set_summary(self.request, issue_key, summary)

    def clone_issue(self, issue_key: str) -> Any:
        """
        Clones an issue identified by the given issue key.

        Arguments:
        - self: The instance of the class.
        - issue_key (str): The key identifying the issue to be cloned.

        Return:
        - Any: The result of cloning the issue.
        """
        return clone_issue(self.request, issue_key)

    def get_sprint(self) -> Any:
        """
        Retrieve the sprint using the request object.

        Arguments:
        - self: The instance of the class.

        Return:
        - Any: The sprint obtained from the request.
        """
        return get_sprint(self.request)


# /* jscpd:ignore-end */
