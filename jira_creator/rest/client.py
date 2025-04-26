#!/usr/bin/env python
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
    def __init__(self) -> None:
        self.jira_url: str = EnvFetcher.get("JIRA_URL")
        self.project_key: str = EnvFetcher.get("PROJECT_KEY")
        self.affects_version: str = EnvFetcher.get("AFFECTS_VERSION")
        self.component_name: str = EnvFetcher.get("COMPONENT_NAME")
        self.priority: str = EnvFetcher.get("PRIORITY")
        self.jpat: str = EnvFetcher.get("JPAT")
        self.epic_field: str = EnvFetcher.get("JIRA_EPIC_FIELD")
        self.board_id: str = EnvFetcher.get("JIRA_BOARD_ID")
        self.fields_cache_path: str = os.path.expanduser("~/.config/rh-issue/fields.json")
        self.is_speaking: bool = False

    def generate_curl_command(
        self, method: str, url: str, headers: Dict[str, str], json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, str]] = None
    ) -> None:
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
            else:
                self.generate_curl_command(
                    method, url, headers, json_data=json_data, params=params
                )
                print(f"Attempt {attempt + 1}: Final failure, raising error")
                raise JiraClientRequestError(
                    f"Failed after {retries} attempts: Status Code {status_code}"
                )

        return None

    def cache_fields(self) -> Optional[Dict[str, Any]]:
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
        fields = self.cache_fields()

        for field in fields:
            if field["id"] == field_id:
                return field["name"]

        return None

    def build_payload(self, summary: str, description: str, issue_type: str) -> Dict[str, Any]:
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
        return get_acceptance_criteria(self.request, issue_key)

    def set_acceptance_criteria(self, issue_key: str, acceptance_criteria: str) -> None:
        return set_acceptance_criteria(self.request, issue_key, acceptance_criteria)

    def get_description(self, issue_key: str) -> str:
        return get_description(self.request, issue_key)

    def update_description(self, issue_key: str, new_description: str) -> None:
        return update_description(self.request, issue_key, new_description)

    def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return create_issue(self.request, payload)

    def change_issue_type(self, issue_key: str, new_type: str) -> None:
        return change_issue_type(self.request, issue_key, new_type)

    def migrate_issue(self, old_key: str, new_type: str) -> None:
        return migrate_issue(
            self.request, self.jira_url, self.build_payload, old_key, new_type
        )

    def add_comment(self, issue_key: str, comment: str) -> None:
        return add_comment(self.request, issue_key, comment)

    def get_current_user(self) -> Any:
        return get_current_user(self.request)

    def get_user(self, str_user: str) -> Any:
        return get_user(self.request, str_user)

    def get_issue_type(self, issue_key: str) -> str:
        return get_issue_type(self.request, issue_key)

    def unassign_issue(self, issue_key: str) -> None:
        return unassign_issue(self.request, issue_key)

    def assign_issue(self, issue_key: str, assignee: str) -> None:
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
        return set_priority(self.request, issue_key, priority)

    def set_sprint(self, issue_key: str, sprint_id: int) -> None:
        return set_sprint(self.request, issue_key, sprint_id)

    def remove_from_sprint(self, issue_key: str) -> None:
        return remove_from_sprint(self.request, issue_key)

    def add_to_sprint(self, issue_key: str, sprint_name: str) -> None:
        return add_to_sprint(self.request, self.board_id, issue_key, sprint_name)

    def set_status(self, issue_key: str, target_status: str) -> None:
        return set_status(self.request, issue_key, target_status)

    def set_story_epic(self, issue_key: str, epic_key: str) -> None:
        return set_story_epic(self.request, issue_key, epic_key)

    def vote_story_points(self, issue_key: str, points: int) -> None:
        return vote_story_points(self.request, issue_key, points)

    def set_story_points(self, issue_key: str, points: int) -> None:
        return set_story_points(self.request, issue_key, points)

    def block_issue(self, issue_key: str, reason: str) -> None:
        return block_issue(self.request, issue_key, reason)

    def unblock_issue(self, issue_key: str) -> None:
        return unblock_issue(self.request, issue_key)

    def blocked(self, project: Optional[str] = None, component: Optional[str] = None, assignee: Optional[str] = None) -> Any:
        return blocked(self.list_issues, project, component, assignee)

    def search_issues(self, jql: str) -> Any:
        return search_issues(self.request, jql)

    def search_users(self, str_user: str) -> Any:
        return search_users(self.request, str_user)

    def view_issue(self, issue_key: str) -> Any:
        return view_issue(self.request, issue_key)

    def add_flag(self, issue_key: str) -> None:
        return add_flag(self.request, issue_key)

    def remove_flag(self, issue_key: str) -> None:
        return remove_flag(self.request, issue_key)

    def list_sprints(self, board_id: int) -> Any:
        return list_sprints(self.request, board_id)

    def set_summary(self, issue_key: str, summary: str) -> None:
        return set_summary(self.request, issue_key, summary)

    def clone_issue(self, issue_key: str) -> Any:
        return clone_issue(self.request, issue_key)

    def get_sprint(self) -> Any:
        return get_sprint(self.request)