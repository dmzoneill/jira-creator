#!/usr/bin/env python
"""
Add comment plugin for jira-creator.

This plugin implements the add-comment command, allowing users to add
comments to Jira issues with optional AI text improvement.
"""

import os
import subprocess
import tempfile
from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import AddCommentError, AiError
from jira_creator.plugins.base import JiraPlugin
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary


class AddCommentPlugin(JiraPlugin):
    """Plugin for adding comments to Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "add-comment"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Add a comment to a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("-t", "--text", help="Comment text (if not provided, opens editor)")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI text improvement")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the add-comment command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful, False otherwise
        """
        # Get comment text
        comment = self._get_comment_text(args)

        if not comment.strip():
            print("⚠️ No comment provided. Skipping.")
            return False

        # Optionally improve with AI
        if not args.no_ai:
            try:
                comment = self._improve_with_ai(comment)
            except AiError as e:
                print(f"⚠️ AI cleanup failed. Using raw comment. Error: {e}")
                # Continue with original comment

        # Add the comment
        try:
            self.rest_operation(client, issue_key=args.issue_key, comment=comment)
            print(f"✅ Comment added to {args.issue_key}")
            return True
        except AddCommentError as e:
            msg = f"❌ Failed to add comment: {e}"
            print(msg)
            raise AddCommentError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to add a comment.

        Arguments:
            client: JiraClient instance
            **kwargs: Must contain 'issue_key' and 'comment'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        comment = kwargs["comment"]

        path = f"/rest/api/2/issue/{issue_key}/comment"
        payload = {"body": comment}

        return client.request("POST", path, json_data=payload)

    def _get_comment_text(self, args: Namespace) -> str:
        """
        Get comment text from arguments or editor.

        Arguments:
            args: Command arguments

        Returns:
            str: Comment text
        """
        if args.text:
            return args.text

        # Get editor function (for testing injection)
        editor_func = self.get_dependency("editor_func", subprocess.call)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write("# Enter comment below\n")
            tmp.flush()

            editor = os.environ.get("EDITOR", "vim")
            editor_func([editor, tmp.name])

            tmp.seek(0)
            return tmp.read()

    def _improve_with_ai(self, comment: str) -> str:
        """
        Improve comment text using AI provider.

        Arguments:
            comment: Original comment text

        Returns:
            str: Improved comment text

        Raises:
            AiError: If AI processing fails
        """
        # Get AI provider (for testing injection)
        ai_provider = self.get_dependency("ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER")))

        prompt = PromptLibrary.get_prompt(IssueType["COMMENT"])
        return ai_provider.improve_text(prompt, comment)
