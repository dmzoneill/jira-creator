# core/jira_env_fetcher.py

import os

from exceptions.exceptions import MissingConfigVariable


class EnvFetcher:
    """Class to fetch and validate Jira-related environment variables."""

    @staticmethod
    def get(var_name):
        """Fetches the value of the environment variable."""
        value = os.getenv(var_name, None)
        if not value:
            raise MissingConfigVariable(
                f"Missing required Jira environment variable: {var_name}"
            )
        return value.strip()

    @staticmethod
    def fetch_all(env_vars):
        """Fetches all required Jira-related environment variables."""
        return {var: EnvFetcher.get(var) for var in env_vars}
