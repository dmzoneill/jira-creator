# core/jira_env_fetcher.py

import os
import sys

from exceptions.exceptions import MissingConfigVariable


class EnvFetcher:
    """Class to fetch and validate Jira-related environment variables."""

    @staticmethod
    def get(var_name):
        """Fetches the value of the environment variable."""

        vars = {
            "JIRA_URL": "https://example.atlassian.net",
            "PROJECT_KEY": "XYZ",
            "AFFECTS_VERSION": "v1.2.3",
            "COMPONENT_NAME": "backend",
            "PRIORITY": "High",
            "JPAT": "dummy-token",
            "JIRA_BOARD_ID": "43123",
            "AI_PROVIDER": "openai",
            "AI_API_KEY": "dsdasdsadsadasdadsa",
            "AI_MODEL": "hhhhhhhhhhhhh",
            "AI_URL": "http://some/url",
            "JIRA_EPIC_FIELD": "customfield_12311140",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_12315940",
            "JIRA_BLOCKED_FIELD": "customfield_12316543",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_12316544",
            "JIRA_STORY_POINTS_FIELD": "customfield_12310243",
            "JIRA_SPRINT_FIELD": "customfield_12310940",
            "VOSK_MODEL": os.path.expanduser("~/.vosk/vosk-model-small-en-us-0.15"),
            "TEMPLATE_DIR": os.path.join(os.path.dirname(__file__), "../templates"),
        }

        value = (
            os.getenv(var_name, None) if "pytest" not in sys.modules else vars[var_name]
        )

        if not value:
            raise MissingConfigVariable(
                f"Missing required Jira environment variable: {var_name}"
            )
        return value.strip()

    @staticmethod
    def fetch_all(env_vars):
        """Fetches all required Jira-related environment variables."""
        return {var: EnvFetcher.get(var) for var in env_vars}
