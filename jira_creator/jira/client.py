import os
from typing import Any, Dict, Optional

import requests

from .actions.add_comment import add_comment as add_comment_action
from .actions.add_to_sprint_by_name import (
    add_to_sprint_by_name as add_to_sprint_by_name_action,
)
from .actions.block_issue import block_issue as block_issue_action
from .actions.blocked import blocked as blocked_action
from .actions.build_payload import build_payload as build_payload_action
from .actions.change_issue_type import change_issue_type as change_issue_type_action
from .actions.create_issue import create_issue as create_issue_action
from .actions.get_current_user import get_current_user as get_current_user_action
from .actions.get_description import get_description as get_description_action
from .actions.get_issue_type import get_issue_type as get_issue_type_action
from .actions.list_issues import list_issues as list_issues_action
from .actions.migrate_issue import migrate_issue as migrate_issue_action
from .actions.remove_from_sprint import remove_from_sprint as remove_from_sprint_action
from .actions.search_issues import search_issues as search_issues_action
from .actions.set_priority import set_priority as set_priority_action
from .actions.set_sprint import set_sprint as set_sprint_action
from .actions.set_status import set_status as set_status_action
from .actions.set_story_points import set_story_points as set_story_points_action
from .actions.unassign_issue import unassign_issue as unassign_issue_action
from .actions.unblock_issue import unblock_issue as unblock_issue_action
from .actions.update_description import update_description as update_description_action
from .actions.vote_story_points import vote_story_points as vote_story_points_action


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
        response = requests.request(
            method, url, headers=headers, json=json, params=params
        )

        if response.status_code >= 400:
            raise Exception(f"JIRA API error ({response.status_code}): {response.text}")
        if not response.text.strip():
            return {}

        return response.json()

    def build_payload(self, summary, description, issue_type):
        return build_payload_action(
            summary,
            description,
            issue_type,
            self.project_key,
            self.affects_version,
            self.component_name,
            self.priority,
            self.epic_field,
        )

    def get_description(self, issue_key):
        return get_description_action(self._request, issue_key)

    def update_description(self, issue_key, new_description):
        update_description_action(self._request, issue_key, new_description)

    def create_issue(self, payload):
        return create_issue_action(self._request, payload)

    def change_issue_type(self, issue_key, new_type):
        return change_issue_type_action(self._request, issue_key, new_type)

    def migrate_issue(self, old_key, new_type):
        return migrate_issue_action(
            self._request, self.jira_url, self.build_payload, old_key, new_type
        )

    def add_comment(self, issue_key, comment):
        add_comment_action(self._request, issue_key, comment)

    def get_current_user(self):
        return get_current_user_action(self._request)

    def get_issue_type(self, issue_key):
        return get_issue_type_action(self._request, issue_key)

    def unassign_issue(self, issue_key):
        return unassign_issue_action(self._request, issue_key)

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
    ):
        return list_issues_action(
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
        )

    def set_priority(self, issue_key, priority):
        set_priority_action(self._request, issue_key, priority)

    def set_sprint(self, issue_key, sprint_id):
        set_sprint_action(self._request, issue_key, sprint_id)

    def remove_from_sprint(self, issue_key):
        remove_from_sprint_action(self._request, issue_key)

    def add_to_sprint_by_name(self, issue_key, sprint_name):
        add_to_sprint_by_name_action(
            self._request, self.board_id, issue_key, sprint_name
        )

    def set_status(self, issue_key, target_status):
        set_status_action(self._request, issue_key, target_status)

    def vote_story_points(self, issue_key, points):
        vote_story_points_action(self._request, issue_key, points)

    def set_story_points(self, issue_key, points):
        set_story_points_action(self._request, issue_key, points)

    def block_issue(self, issue_key, reason):
        block_issue_action(self._request, issue_key, reason)

    def unblock_issue(self, issue_key):
        unblock_issue_action(self._request, issue_key)

    def blocked(self, project=None, component=None, user=None):
        return blocked_action(self.list_issues, project, component, user)

    def search_issues(self, jql):
        return search_issues_action(self._request, jql)
