#!/usr/bin/env python
"""
This module provides a class, EnvFetcher, to fetch and validate Jira-related environment variables. It includes methods
to fetch the value of a specific environment variable and to fetch all required Jira-related environment variables.

The EnvFetcher class offers the following functionality:

- Fetch individual environment variable values, with validation to ensure they are set.
- Retrieve all specified Jira-related environment variables in a single call.

Attributes include various configuration options needed for interacting with Jira, such as the Jira instance URL,
project key, personal access token, and custom field identifiers. The class is designed to ensure that all necessary
environment variables are available for proper functionality.
"""

# core/jira_env_fetcher.py

import os
import sys
from typing import Dict, List, Optional

from exceptions.exceptions import MissingConfigVariable


class EnvFetcher:
    """
    Class to fetch and validate Jira-related environment variables.

    Attributes:
    - JIRA_URL (str): The URL of the Jira instance.
    - PROJECT_KEY (str): The key of the Jira project.
    - AFFECTS_VERSION (str): The affected version of the project.
    - COMPONENT_NAME (str): The name of the component.
    - PRIORITY (str): The priority level of the issue.
    - JPAT (str): The Jira personal access token.
    - JIRA_BOARD_ID (str): The ID of the Jira board.
    - AI_PROVIDER (str): The provider of the AI service.
    - AI_API_KEY (str): The API key for the AI service.
    - AI_MODEL (str): The model used for AI processing.
    - AI_URL (str): The URL for the AI service.
    - JIRA_EPIC_FIELD (str): The custom field for Jira epics.
    - JIRA_ACCEPTANCE_CRITERIA_FIELD (str): The custom field for acceptance criteria.
    - JIRA_BLOCKED_FIELD (str): The custom field for blocked status.
    - JIRA_BLOCKED_REASON_FIELD (str): The custom field for blocked reasons.
    - JIRA_STORY_POINTS_FIELD (str): The custom field for story points.
    - JIRA_SPRINT_FIELD (str): The custom field for sprints.
    - VOSK_MODEL (str): The path to the Vosk model file.
    - TEMPLATE_DIR (str): The directory path for templates.

    Methods:
    - get(var_name): Fetches the value of the specified environment variable.
    - fetch_all(env_vars): Fetches all specified Jira-related environment variables.
    """

    vars: Dict[str, str] = {
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
        "JIRA_VIEW_COLUMNS": "key,issuetype,status,priority,summary,assignee,reporter,sprint,JIRA_STORY_POINTS_FIELD",
        "JIRA_EPIC_FIELD": "customfield_12311140",
        "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_12315940",
        "JIRA_BLOCKED_FIELD": "customfield_12316543",
        "JIRA_BLOCKED_REASON_FIELD": "customfield_12316544",
        "JIRA_STORY_POINTS_FIELD": "customfield_12310243",
        "JIRA_SPRINT_FIELD": "customfield_12310940",
        "VOSK_MODEL": os.path.expanduser("~/.vosk/vosk-model-small-en-us-0.15"),
        "TEMPLATE_DIR": os.path.join(os.path.dirname(__file__), "../templates"),
    }

    @staticmethod
    def get(var_name: str) -> str:
        """
        Fetches the value of the environment variable.

        Arguments:
        - var_name (str): The name of the environment variable to retrieve the value for.
        """

        value: Optional[str] = (
            os.getenv(var_name)
            if "pytest" not in sys.modules
            else EnvFetcher.vars[var_name]
        )
        default: str = os.path.join(os.path.dirname(__file__), "../templates")
        value = default if var_name == "TEMPLATE_DIR" and value is None else value

        if not value:
            raise MissingConfigVariable(
                f"Missing required Jira environment variable: {var_name}"
            )
        return value.strip()

    @staticmethod
    def fetch_all(env_vars: List[str]) -> Dict[str, str]:
        """
        Fetches all required Jira-related environment variables.

        Arguments:
        - env_vars (list): A list of environment variables to fetch.

        Return:
        - dict: A dictionary containing the fetched environment variables as key-value pairs.
        """

        vars = env_vars if len(env_vars) > 0 else EnvFetcher.vars

        return {var: EnvFetcher.get(var) for var in vars}
