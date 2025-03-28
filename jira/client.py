import os
import requests
from typing import Any, Dict, List, Optional


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

        if not all([self.jira_url, self.project_key, self.jpat]):
            raise EnvironmentError(
                "Missing required JIRA configuration in environment variables."
            )

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        allow_204: bool = False,
    ) -> Dict[str, Any]:
        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }
        response = requests.request(
            method, url, headers=headers, json=json, params=params
        )

        if allow_204 and response.status_code == 204:
            return {}
        if response.status_code >= 400:
            raise Exception(f"JIRA API error ({response.status_code}): {response.text}")
        if not response.text.strip():
            return {}

        return response.json()

    def build_payload(
        self, summary: str, description: str, issue_type: str
    ) -> Dict[str, Any]:
        fields: Dict[str, Any] = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type.capitalize()},
            "priority": {"name": self.priority},
            "versions": [{"name": self.affects_version}],
            "components": [{"name": self.component_name}],
        }

        if issue_type.lower() == "epic":
            fields[self.epic_field] = summary

        return {"fields": fields}

    def get_description(self, issue_key: str) -> str:
        return self._request("GET", f"/rest/api/2/issue/{issue_key}")["fields"].get(
            "description", ""
        )

    def update_description(self, issue_key: str, new_description: str) -> None:
        self._request(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json={"fields": {"description": new_description}},
            allow_204=True,
        )

    def create_issue(self, payload: Dict[str, Any]) -> str:
        return self._request("POST", "/rest/api/2/issue/", json=payload).get("key", "")

    def change_issue_type(self, issue_key: str, new_type: str) -> bool:
        try:
            issue_data = self._request("GET", f"/rest/api/2/issue/{issue_key}")
            is_subtask = issue_data["fields"]["issuetype"]["subtask"]
            payload: Dict[str, Any] = {
                "fields": {"issuetype": {"name": new_type.capitalize()}}
            }
            if is_subtask:
                payload["update"] = {"parent": [{"remove": {}}]}

            self._request(
                "PUT", f"/rest/api/2/issue/{issue_key}", json=payload, allow_204=True
            )
            return True
        except Exception as e:
            print(f"❌ Failed to change issue type: {e}")
            return False

    def migrate_issue(self, old_key: str, new_type: str) -> str:
        fields = self._request("GET", f"/rest/api/2/issue/{old_key}")["fields"]
        summary = fields.get("summary", f"Migrated from {old_key}")
        description = fields.get("description", f"Migrated from {old_key}")

        payload = self.build_payload(summary, description, new_type)
        new_key = self._request("POST", "/rest/api/2/issue/", json=payload)["key"]

        self._request(
            "POST",
            f"/rest/api/2/issue/{old_key}/comment",
            json={
                "body": f"Migrated to [{new_key}]({self.jira_url}/browse/{new_key}) as a {new_type.upper()}."
            },
        )

        transitions = self._request("GET", f"/rest/api/2/issue/{old_key}/transitions")[
            "transitions"
        ]
        transition_id = next(
            (
                t["id"]
                for t in transitions
                if t["name"].lower() in ["done", "closed", "cancelled"]
            ),
            None,
        )
        if not transition_id and transitions:
            transition_id = transitions[0]["id"]

        if transition_id:
            self._request(
                "POST",
                f"/rest/api/2/issue/{old_key}/transitions",
                json={"transition": {"id": transition_id}},
            )

        return new_key

    def get_current_user(self) -> str:
        user = self._request("GET", "/rest/api/2/myself")
        return user.get("name") or user.get("accountId")

    def unassign_issue(self, issue_key: str) -> bool:
        try:
            self._request(
                "PUT",
                f"/rest/api/2/issue/{issue_key}",
                json={"fields": {"assignee": None}},
                allow_204=True,
            )
            return True
        except Exception as e:
            print(f"❌ Failed to unassign issue {issue_key}: {e}")
            return False

    def list_issues(
        self,
        project: Optional[str] = None,
        component: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        jql_parts = []
        if project := project or self.project_key:
            jql_parts.append(f'project="{project}"')
        if component := component or self.component_name:
            jql_parts.append(f'component="{component}"')
        if username := assignee or self.get_current_user():
            jql_parts.append(f'assignee="{username}"')
        jql = (
            " AND ".join(jql_parts) + ' AND status NOT IN ("Closed", "Done", "Cancelled")'
        )

        params = {
            "jql": jql,
            "fields": "summary,status,assignee,priority,customfield_12310243,customfield_12310940",
            "maxResults": 200,
        }
        return self._request("GET", "/rest/api/2/search", params=params).get(
            "issues", []
        )

    def set_priority(self, issue_key: str, priority: str) -> None:
        self._request(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json={"fields": {"priority": {"name": priority}}},
            allow_204=True,
        )

    def set_sprint(self, issue_key: str, sprint_id: Optional[int]) -> None:
        payload = {
            "fields": {
                "customfield_12310940": None if not sprint_id else [str(sprint_id)]
            }
        }
        self._request(
            "PUT", f"/rest/api/2/issue/{issue_key}", json=payload, allow_204=True
        )

    def remove_from_sprint(self, issue_key: str) -> None:
        try:
            self._request(
                "POST", "/rest/agile/1.0/backlog/issue", json={"issues": [issue_key]}
            )
            print(f"✅ Moved {issue_key} to backlog")
        except Exception as e:
            print(f"❌ Failed to remove from sprint: {e}")

    def add_to_sprint(self, issue_key: str, sprint_id: int) -> None:
        try:
            self._request(
                "POST",
                f"/rest/agile/1.0/sprint/{sprint_id}/issue",
                json={"issues": [issue_key]},
            )
            print(f"✅ Added {issue_key} to sprint ID {sprint_id}")
        except Exception as e:
            raise Exception(f"❌ Failed to add issue to sprint: {e}")

    def add_to_sprint_by_name(self, issue_key: str, sprint_name: str) -> None:
        if not self.board_id:
            raise Exception("❌ JIRA_BOARD_ID not set in environment")

        sprints = self._request(
            "GET", f"/rest/agile/1.0/board/{self.board_id}/sprint"
        ).get("values", [])
        sprint_id = next((s["id"] for s in sprints if s["name"] == sprint_name), None)

        if not sprint_id:
            raise Exception(f"❌ Could not find sprint named '{sprint_name}'")

        self._request(
            "POST",
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            json={"issues": [issue_key]},
        )
        print(
            f"✅ Added {issue_key} to sprint '{sprint_name}' on board {self.board_id}"
        )

    def set_status(self, issue_key: str, target_status: str) -> None:
        transitions = self._request(
            "GET", f"/rest/api/2/issue/{issue_key}/transitions"
        ).get("transitions", [])
        transition_id = next(
            (
                t["id"]
                for t in transitions
                if t["name"].lower() == target_status.lower()
            ),
            None,
        )

        if not transition_id:
            raise Exception(f"❌ Transition to status '{target_status}' not found")

        self._request(
            "POST",
            f"/rest/api/2/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        print(f"✅ Changed status of {issue_key} to '{target_status}'")
