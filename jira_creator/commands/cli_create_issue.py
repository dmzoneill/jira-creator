"""
This module provides a CLI tool for creating Jira issues with enhanced functionality.
It includes functions for loading templates, interacting with the user to input data, editing descriptions,
improving text using AI, building Jira payloads, and creating Jira issues.
Exceptions are handled for file not found, AI errors, and create issue errors.
"""

import json
import os
import subprocess
import tempfile

from exceptions.exceptions import AiError, CreateIssueError
from rest.prompts import IssueType, PromptLibrary
from templates.template_loader import TemplateLoader


def cli_create_issue(jira, ai_provider, default_prompt, template_dir, args):
    """
    Creates a new issue in Jira based on a template.

    Arguments:
    - jira (JIRA): An instance of the JIRA class for interacting with the Jira API.
    - ai_provider (str): The AI provider to use for generating content.
    - default_prompt (str): The default prompt to use for the issue description.
    - template_dir (str): The directory where the issue templates are stored.
    - args (Namespace): Command-line arguments containing the type of the issue.

    Exceptions:
    - FileNotFoundError: Raised when the template file specified by 'args.type' is not found in 'template_dir'.

    Side Effects:
    - Prints an error message if the template file is not found.
    - Raises a FileNotFoundError exception with the original error message.

    """

    try:
        template = TemplateLoader(template_dir, args.type)
        fields = template.get_fields()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise FileNotFoundError(e) from e

    inputs = (
        {field: input(f"{field}: ") for field in fields}
        if not args.edit
        else {field: f"# {field}" for field in fields}
    )

    description = template.render_description(inputs)

    if args.edit is not None:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".tmp", delete=False) as tmp:
            tmp.write(description)
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            description = tmp.read()

    enum_type = IssueType[args.type.upper()]
    prompt = PromptLibrary.get_prompt(enum_type)

    try:
        description = ai_provider.improve_text(prompt, description)
    except AiError as e:
        msg = f"⚠️ AI cleanup failed. Using original text. Error: {e}"
        print(msg)
        raise AiError(e) from e

    payload = jira.build_payload(args.summary, description, args.type)

    if args.dry_run:
        print("📦 DRY RUN ENABLED")
        print("---- Description ----")
        print(description)
        print("---- Payload ----")
        print(json.dumps(payload, indent=2))
        return

    try:
        key = jira.create_issue(payload)
        print(f"✅ Created: {jira.jira_url}/browse/{key}")
        return key
    except CreateIssueError as e:
        msg = f"❌ Failed to create issue: {e}"
        print(msg)
        raise CreateIssueError(e) from e
