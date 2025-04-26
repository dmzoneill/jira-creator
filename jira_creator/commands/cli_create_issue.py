#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) tool for creating and managing Jira issues with enhanced features.

Key functionalities include:
- Loading issue templates from a specified directory.
- Interacting with users to gather input for issue creation.
- Editing issue descriptions prior to submission.
- Utilizing AI to improve text descriptions.
- Building payloads for Jira API requests.
- Handling exceptions related to file operations, AI processing, and issue creation.

The main function, `cli_create_issue`, orchestrates the process of creating a new Jira issue based on user input and
templates, while managing potential errors and providing informative output.
"""

import json
import os
import subprocess
import tempfile
from argparse import Namespace
from typing import Any, Dict, Optional

from exceptions.exceptions import AiError, CreateIssueError
from providers.ai_provider import AIProvider
from rest.client import JiraClient
from rest.prompts import IssueType, PromptLibrary
from templates.template_loader import TemplateLoader


def cli_create_issue(
    jira: JiraClient, ai_provider: AIProvider, template_dir: str, args: Namespace
) -> Optional[str]:
    """
    Creates a new issue in Jira based on a template.

    Arguments:
    - jira (Any): An instance of the JIRA class for interacting with the Jira API.
    - ai_provider (Any): The AI provider to use for generating content.
    - template_dir (str): The directory where the issue templates are stored.
    - args (Any): Command-line arguments containing the type of the issue.

    Exceptions:
    - FileNotFoundError: Raised when the template file specified by 'args.type' is not found in 'template_dir'.

    Side Effects:
    - Prints an error message if the template file is not found.
    - Raises a FileNotFoundError exception with the original error message.
    - Prints warnings or errors related to AI cleanup failure or issue creation failure.
    """

    try:
        template = TemplateLoader(template_dir, args.type)
        fields: Dict[str, str] = template.get_fields()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise FileNotFoundError(e) from e

    inputs: Dict[str, str] = (
        {field: input(f"{field}: ") for field in fields}
        if not args.edit
        else {field: f"# {field}" for field in fields}
    )

    description: str = template.render_description(inputs)

    if args.edit is not None:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".tmp", delete=False) as tmp:
            tmp.write(description)
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            description = tmp.read()

    enum_type: IssueType = IssueType[args.type.upper()]
    prompt: str = PromptLibrary.get_prompt(enum_type)

    try:
        description = ai_provider.improve_text(prompt, description)
    except AiError as e:
        msg = f"⚠️ AI cleanup failed. Using original text. Error: {e}"
        print(msg)
        raise AiError(e) from e

    payload: Dict[str, Any] = jira.build_payload(args.summary, description, args.type)

    if args.dry_run:
        print("📦 DRY RUN ENABLED")
        print("---- Description ----")
        print(description)
        print("---- Payload ----")
        print(json.dumps(payload, indent=2))
        return None

    try:
        key: str = jira.create_issue(payload)
        print(f"✅ Created: {jira.jira_url}/browse/{key}")
        return key
    except CreateIssueError as e:
        msg = f"❌ Failed to create issue: {e}"
        print(msg)
        raise CreateIssueError(e) from e
