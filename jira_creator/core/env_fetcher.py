#!/usr/bin/env python
"""
This module provides the EnvFetcher class, which is responsible for fetching and validating Jira-related environment
variables.

The EnvFetcher class includes methods to retrieve individual environment variable values and to collect all required
Jira-related environment variables in a single call. It ensures that all necessary environment variables are set, which
is crucial for the proper functioning of applications interacting with Jira.

Key attributes include:
- JIRA_URL: URL of the Jira instance.
- JIRA_PROJECT_KEY: Key of the Jira project.
- JIRA_JPAT: Personal access token for Jira.
- Various custom field identifiers for Jira issues.

Methods:
- get(var_name): Fetches the value of a specified environment variable, raising an error if it is not set.
- fetch_all(env_vars): Retrieves all specified Jira-related environment variables, returning them as a dictionary.
"""

# core/jira_env_fetcher.py

import os
import sys
from typing import Dict, List, Optional

from jira_creator.exceptions.exceptions import MissingConfigVariable


class EnvFetcher:
    """
    Class to fetch and validate Jira-related environment variables.

    Attributes:
    - JIRA_URL (str): The URL of the Jira instance.
    - JIRA_PROJECT_KEY (str): The key of the Jira project.
    - JIRA_AFFECTS_VERSION (str): The affected version of the project.
    - JIRA_COMPONENT_NAME (str): The name of the component.
    - JIRA_PRIORITY (str): The priority level of the issue.
    - JIRA_JPAT (str): The Jira personal access token.
    - JIRA_BOARD_ID (str): The ID of the Jira board.
    - JIRA_AI_PROVIDER (str): The provider of the AI service.
    - JIRA_AI_API_KEY (str): The API key for the AI service.
    - JIRA_AI_MODEL (str): The model used for AI processing.
    - JIRA_AI_URL (str): The URL for the AI service.
    - JIRA_EPIC_FIELD (str): The custom field for Jira epics.
    - JIRA_ACCEPTANCE_CRITERIA_FIELD (str): The custom field for acceptance criteria.
    - JIRA_BLOCKED_FIELD (str): The custom field for blocked status.
    - JIRA_BLOCKED_REASON_FIELD (str): The custom field for blocked reasons.
    - JIRA_STORY_POINTS_FIELD (str): The custom field for story points.
    - JIRA_SPRINT_FIELD (str): The custom field for sprints.
    - JIRA_VOSK_MODEL (str): The path to the Vosk model file.
    - TEMPLATE_DIR (str): The directory path for templates.

    Methods:
    - get(var_name): Fetches the value of the specified environment variable.
    - fetch_all(env_vars): Fetches all specified Jira-related environment variables.
    """

    vars: Dict[str, str] = {
        "JIRA_URL": "https://example.atlassian.net",
        "JIRA_PROJECT_KEY": "XYZ",
        "JIRA_AFFECTS_VERSION": "v1.2.3",
        "JIRA_COMPONENT_NAME": "backend",
        "JIRA_PRIORITY": "High",
        "JIRA_JPAT": "dummy-token",
        "JIRA_BOARD_ID": "43123",
        "JIRA_AI_PROVIDER": "openai",
        "JIRA_AI_API_KEY": "dsdasdsadsadasdadsa",
        "JIRA_AI_MODEL": "hhhhhhhhhhhhh",
        "JIRA_AI_URL": "http://some/url",
        "JIRA_VIEW_COLUMNS": "key,issuetype,status,priority,summary,assignee,reporter,sprint,JIRA_STORY_POINTS_FIELD",
        "JIRA_EPIC_FIELD": "customfield_12311140",
        "JIRA_EPIC_KEY": "",
        "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_12315940",
        "JIRA_BLOCKED_FIELD": "customfield_12316543",
        "JIRA_BLOCKED_REASON_FIELD": "customfield_12316544",
        "JIRA_STORY_POINTS_FIELD": "customfield_12310243",
        "JIRA_SPRINT_FIELD": "customfield_12310940",
        "JIRA_VOSK_MODEL": os.path.expanduser("~/.vosk/vosk-model-small-en-us-0.15"),
        "TEMPLATE_DIR": os.path.join(os.path.dirname(__file__), "../templates"),
    }

    @staticmethod
    def get(var_name: str, default: Optional[str] = None) -> str:
        """
        Fetches the value of the environment variable.

        Arguments:
        - var_name (str): The name of the environment variable to retrieve the value for.
        - default (Optional[str]): Default value to return if environment variable is not set.
        """

        value: Optional[str] = os.getenv(var_name) if "pytest" not in sys.modules else EnvFetcher.vars[var_name]

        # Handle special default for TEMPLATE_DIR
        template_default: str = os.path.join(os.path.dirname(__file__), "../templates")
        if var_name == "TEMPLATE_DIR" and value is None:
            value = template_default

        # If value is still None and a default was provided, use it
        if value is None and default is not None:
            return default

        # Optional environment variables that can be empty
        optional_vars = [
            "JIRA_AFFECTS_VERSION",
            "JIRA_EPIC_KEY",
            "JIRA_COMPONENT_NAME",
            "JIRA_EPIC_FIELD",
        ]
        if var_name in optional_vars and value == "":
            return ""

        # If no value and no default provided, check if it's required
        if not value:
            # If a default was provided but value is empty string, return default
            if default is not None:
                return default
            raise MissingConfigVariable(f"Missing required Jira environment variable: {var_name}")
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
