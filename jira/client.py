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

    def build_payload(self, summary: str, description: str, issue_type: str) -> dict:
        return {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type.capitalize()},
                "priority": {"name": self.priority},
                "versions": [{"name": self.affects_version}],
                "components": [{"name": self.component_name}],
            }
        }

    def create_issue(self, payload: dict) -> str:
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.jira_url}/rest/api/2/issue/", headers=headers, json=payload
        )

        if response.status_code == 201:
            return response.json().get("key")
        else:
            raise Exception(
                f"Failed to create issue: {response.status_code} - {response.text}"
            )
