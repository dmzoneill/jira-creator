#!/usr/bin/env python
"""
This module provides a function to interact with Jira by adding comments to an issue. It prompts the user to enter a
comment either directly or through a text editor if not provided. The comment is then processed by an AI provider to
improve the text before being added to the specified Jira issue.

Functions:
- cli_add_comment(jira, ai_provider, comment_prompt, args): Adds a comment to a Jira issue after processing it with an
AI provider.

Exceptions:
- AddCommentError: Raised when there is an issue adding a comment to the Jira issue.
- AiError: Raised when there is an error with the AI processing the comment.
"""

import os
import subprocess
import tempfile
from argparse import Namespace

from exceptions.exceptions import AddCommentError, AiError
from providers.ai_provider import AIProvider
from rest.client import JiraClient


def cli_add_comment(
    jira: JiraClient, ai_provider: AIProvider, comment_prompt: str, args: Namespace
) -> bool:
    """
    Add a comment to a Jira issue via the command line interface.

    Arguments:
    - jira (Any): An instance of the JIRA class for interacting with Jira.
    - ai_provider (Any): The AI provider to use for processing the comment.
    - comment_prompt (str): The prompt message for entering the comment.
    - args (Any): Command-line arguments parsed by argparse.

    Side Effects:
    - If args.text is provided, the comment is set to args.text.
    - If args.text is not provided, a temporary Markdown file is created with a prompt message.
    The user is prompted to enter the comment using the default text editor (or vim if not set).
    The content of the temporary file is then read as the comment.

    Note: This function is designed for command-line interaction to add comments to Jira issues.
    """

    if args.text:
        comment: str = args.text
    else:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write("# Enter comment below\n")
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            comment = tmp.read()

    if not comment.strip():
        print("⚠️ No comment provided. Skipping.")
        return False

    try:
        cleaned: str = ai_provider.improve_text(comment_prompt, comment)
    except AiError as e:
        msg = f"⚠️ AI cleanup failed. Using raw comment. Error: {e}"
        print(msg)
        raise AiError(msg) from e

    try:
        jira.add_comment(args.issue_key, cleaned)
        print(f"✅ Comment added to {args.issue_key}")
        return True
    except AddCommentError as e:
        msg = f"❌ Failed to add comment: {e}"
        print(msg)
        raise AddCommentError(e) from e
