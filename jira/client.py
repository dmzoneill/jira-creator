import os
import requests


class JiraClient:
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.project_key = os.getenv("PROJECT_KEY")
        self.affects_version = os.getenv("AFFECTS_VERSION")
        self.component_name = os.getenv("COMPONENT_NAME")
        self.priority = os.getenv("PRIORITY")
        self.jpat = os.getenv("JPAT")

        if not self.jira_url or not self.project_key or not self.jpat:
            raise EnvironmentError(
                "Missing required JIRA configuration in environment variables."
            )

    def _request(self, method: str, path: str, json=None, allow_204=False):
        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }

        response = requests.request(method, url, headers=headers, json=json)

        if allow_204 and response.status_code == 204:
            return None

        if response.status_code >= 400:
            raise Exception(f"JIRA API error ({response.status_code}): {response.text}")

        return response.json()

    def build_payload(self, summary: str, description: str, issue_type: str) -> dict:
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type.capitalize()},
            "priority": {"name": self.priority},
            "versions": [{"name": self.affects_version}],
            "components": [{"name": self.component_name}],
        }

        if issue_type.lower() == "epic":
            epic_field = os.getenv("JIRA_EPIC_NAME_FIELD", "customfield_12311141")
            fields[epic_field] = summary

        return {"fields": fields}

    def get_description(self, issue_key: str) -> str:
        issue = self._request("GET", f"/rest/api/2/issue/{issue_key}")
        return issue["fields"].get("description", "")

    def update_description(self, issue_key: str, new_description: str):
        payload = {"fields": {"description": new_description}}
        self._request(
            "PUT", f"/rest/api/2/issue/{issue_key}", json=payload, allow_204=True
        )

    def create_issue(self, payload: dict) -> str:
        data = self._request("POST", "/rest/api/2/issue/", json=payload)
        return data.get("key")

    def change_issue_type(self, issue_key: str, new_type: str) -> bool:
        try:
            issue_data = self._request("GET", f"/rest/api/2/issue/{issue_key}")
            is_subtask = issue_data["fields"]["issuetype"]["subtask"]

            payload = {"fields": {"issuetype": {"name": new_type.capitalize()}}}

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
        old_issue = self._request("GET", f"/rest/api/2/issue/{old_key}")
        fields = old_issue["fields"]

        summary = fields.get("summary", f"Migrated from {old_key}")
        description = fields.get("description", f"Migrated from {old_key}")

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": new_type.capitalize()},
                "priority": {"name": self.priority},
                "versions": [{"name": self.affects_version}],
                "components": [{"name": self.component_name}],
            }
        }

        new_key = self._request("POST", "/rest/api/2/issue/", json=payload)["key"]

        comment = {
            "body": f"Migrated to [{new_key}]({self.jira_url}/browse/{new_key}) as a {new_type.upper()}."
        }
        self._request("POST", f"/rest/api/2/issue/{old_key}/comment", json=comment)

        transitions = self._request("GET", f"/rest/api/2/issue/{old_key}/transitions")[
            "transitions"
        ]

        transition_id = None
        for t in transitions:
            if t["name"].lower() in ["done", "closed", "cancelled"]:
                transition_id = t["id"]
                break
        if not transition_id and transitions:
            transition_id = transitions[0]["id"]

        if transition_id:
            transition_payload = {"transition": {"id": transition_id}}
            self._request(
                "POST",
                f"/rest/api/2/issue/{old_key}/transitions",
                json=transition_payload,
            )

        return new_key
