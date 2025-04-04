import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

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
    list_issues,
    migrate_issue,
    remove_from_sprint,
    search_issues,
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
        self.jira_url = os.getenv("JIRA_URL")
        self.project_key = os.getenv("PROJECT_KEY")
        self.affects_version = os.getenv("AFFECTS_VERSION")
        self.component_name = os.getenv("COMPONENT_NAME")
        self.priority = os.getenv("PRIORITY")
        self.jpat = os.getenv("JPAT")
        self.epic_field = os.getenv("JIRA_EPIC_NAME_FIELD", "customfield_12311141")
        self.board_id = os.getenv("JIRA_BOARD_ID")
        self.fields_cache_path = os.path.expanduser("~/.config/rh-issue/fields.json")

        if not all(
            [
                self.jira_url,
                self.project_key,
                self.affects_version,
                self.component_name,
                self.priority,
                self.jpat,
                self.epic_field,
                self.board_id,
            ]
        ):
            raise EnvironmentError(
                "Missing required JIRA configuration in environment variables."
            )

    def is_running_under_pytest(self):
        return "pytest" in sys.modules

    def ensure_requests_is_mocked(self):
        if self.is_running_under_pytest():
            # Check if requests.request is mocked by pytest
            if "mock_calls" not in dir(requests.request):
                raise Exception(
                    "Running under pytest but requests is not mocked. "
                    "This would result in an API query. Requests should be mocked."
                )

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }

        self.ensure_requests_is_mocked()

        response = requests.request(
            method, url, headers=headers, json=json, params=params
        )

        if response.status_code >= 400:
            raise Exception(f"JIRA API error ({response.status_code}): {response.text}")
        if not response.text.strip():
            return {}

        return response.json()

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
        return list_issues(
            self._request,
            self.get_current_user,
            self.project_key,
            self.component_name,
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

    def blocked(self, project=None, component=None, user=None):
        return blocked(self.list_issues, project, component, user)

    def search_issues(self, jql):
        return search_issues(self._request, jql)

    def view_issue(self, issue_key):
        return view_issue(self._request, issue_key)
