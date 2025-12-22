#!/usr/bin/env python
"""
Open issue plugin for jira-creator.

This plugin implements the open-issue command, allowing users to open
Jira issues in their default web browser.
"""

import subprocess
import sys
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin


class OpenIssueError(Exception):
    """Exception raised when opening an issue fails."""


class OpenIssuePlugin(JiraPlugin):
    """Plugin for opening Jira issues in web browser."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "open-issue"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Open a Jira issue in your web browser"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Utilities"

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "OpenIssueError": OpenIssueError,
        }

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["open-issue AAP-12345"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the open-issue command.

        Arguments:
            client: JiraClient instance (not used)
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Get Jira URL from environment
            jira_url = EnvFetcher.get("JIRA_URL")
            if not jira_url:
                raise OpenIssueError("JIRA_URL not set in environment")

            # Build issue URL
            issue_url = f"{jira_url}/browse/{args.issue_key}"

            # Open in browser based on platform
            if sys.platform == "darwin":  # macOS
                with subprocess.Popen(["open", issue_url]):
                    pass
            elif sys.platform in ("linux", "linux2"):  # Linux
                with subprocess.Popen(["xdg-open", issue_url]):
                    pass
            elif sys.platform == "win32":  # Windows
                with subprocess.Popen(["start", issue_url], shell=True):
                    pass
            else:
                raise OpenIssueError(f"Unsupported platform: {sys.platform}")

            print(f"🌐 Opening {issue_url} in browser...")
            return True

        except OpenIssueError as e:
            msg = f"❌ Failed to open issue: {e}"
            print(msg)
            raise OpenIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        No REST operation needed for this command.

        Arguments:
            client: JiraClient instance
            **kwargs: Not used

        Returns:
            Empty dict
        """
        return {}
