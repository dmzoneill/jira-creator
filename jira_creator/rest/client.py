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
)


class JiraClient:
    def __init__(self):
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

    def generate_curl_command(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> None:
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

    def __request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> tuple:
        """Core request logic. Returns a tuple (status_code, result)."""
        try:
            response = requests.request(
                method, url, headers=headers, json=json, params=params, timeout=10
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
            raise JiraClientRequestError(f"Request failed: {e}")

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Handles retries and delegates the request to __request."""
        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }

        retries = 3
        delay = 2

        for attempt in range(retries):
            status_code, result = self.__request(
                method, url, headers, json=json, params=params
            )

            if 200 <= status_code < 300:  # Handle all 2xx status codes as success
                return result

            if attempt < retries - 1:
                print(f"Attempt {attempt + 1}: Sleeping before retry...")
                time.sleep(delay)
            else:
                # Generate a cURL command for debugging failed requests
                self.generate_curl_command(
                    method, url, headers, json_data=json, params=params
                )

                print(f"Attempt {attempt + 1}: Final failure, raising error")
                raise JiraClientRequestError(
                    f"Failed after {retries} attempts: Status Code {status_code}"
                )

        return None  # Unreachable code  # pragma: no cover

    def cache_fields(self):
        # Check if the cache file exists and is less than 24 hours old
        if os.path.exists(self.fields_cache_path):
            file_age = time.time() - os.path.getmtime(self.fields_cache_path)
            if file_age < 86400:  # 86400 seconds = 24 hours
                with open(self.fields_cache_path, "r") as f:
                    return json.load(f)

        # If the file doesn't exist or is older than 24 hours, update it
        fields = self._request("GET", "/rest/api/2/field")

        # Make sure the directory exists
        os.makedirs(os.path.dirname(self.fields_cache_path), exist_ok=True)

        with open(self.fields_cache_path, "w") as f:
            json.dump(fields, f, indent=4)

        return fields

    def get_field_name(self, field_id):
        # Cache the fields (loads from cache or updates if necessary)
        fields = self.cache_fields()

        # Find the field with the matching ID
        for field in fields:
            if field["id"] == field_id:
                return field["name"]

        return None  # Return None if no field with the given ID is found

    def build_payload(self, summary, description, issue_type):
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
        return get_acceptance_criteria(self._request, issue_key)

    def set_acceptance_criteria(self, issue_key, acceptance_criteria):
        return set_acceptance_criteria(self._request, issue_key, acceptance_criteria)

    def get_description(self, issue_key):
        return get_description(self._request, issue_key)

    def update_description(self, issue_key, new_description):
        return update_description(self._request, issue_key, new_description)

    def create_issue(self, payload):
        return create_issue(self._request, payload)

    def change_issue_type(self, issue_key, new_type):
        return change_issue_type(self._request, issue_key, new_type)

    def migrate_issue(self, old_key, new_type):
        return migrate_issue(
            self._request, self.jira_url, self.build_payload, old_key, new_type
        )

    def add_comment(self, issue_key, comment):
        return add_comment(self._request, issue_key, comment)

    def get_current_user(self):
        return get_current_user(self._request)

    def get_user(self, str):
        return get_user(self._request, str)

    def get_issue_type(self, issue_key):
        return get_issue_type(self._request, issue_key)

    def unassign_issue(self, issue_key):
        return unassign_issue(self._request, issue_key)

    def assign_issue(self, issue_key, assignee):
        return assign_issue(self._request, issue_key, assignee)

    def list_issues(
        self,
        project=None,
        component=None,
        assignee=None,
        status=None,
        summary=None,
        show_reason=False,
        blocked=False,
        unblocked=False,
        reporter=None,
    ):
        component = component if component is not None else self.component_name
        project = project if project is not None else self.project_key

        return list_issues(
            self._request,
            self.get_current_user,
            project,
            component,
            assignee,
            status,
            summary,
            show_reason,
            blocked,
            unblocked,
            reporter,
        )

    def set_priority(self, issue_key, priority):
        return set_priority(self._request, issue_key, priority)

    def set_sprint(self, issue_key, sprint_id):
        return set_sprint(self._request, issue_key, sprint_id)

    def remove_from_sprint(self, issue_key):
        return remove_from_sprint(self._request, issue_key)

    def add_to_sprint_by_name(self, issue_key, sprint_name):
        return add_to_sprint_by_name(
            self._request, self.board_id, issue_key, sprint_name
        )

    def set_status(self, issue_key, target_status):
        return set_status(self._request, issue_key, target_status)

    def set_story_epic(self, issue_key, epic_key):
        return set_story_epic(self._request, issue_key, epic_key)

    def vote_story_points(self, issue_key, points):
        return vote_story_points(self._request, issue_key, points)

    def set_story_points(self, issue_key, points):
        return set_story_points(self._request, issue_key, points)

    def block_issue(self, issue_key, reason):
        return block_issue(self._request, issue_key, reason)

    def unblock_issue(self, issue_key):
        return unblock_issue(self._request, issue_key)

    def blocked(self, project=None, component=None, assignee=None):
        return blocked(self.list_issues, project, component, assignee)

    def search_issues(self, jql):
        return search_issues(self._request, jql)

    def search_users(self, str):
        return search_users(self._request, str)

    def view_issue(self, issue_key):
        return view_issue(self._request, issue_key)
