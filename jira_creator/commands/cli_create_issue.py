import json
import os
import subprocess
import tempfile

from exceptions.exceptions import AiError, CreateIssueError
from rest.prompts import IssueType, PromptLibrary
from templates.template_loader import TemplateLoader


def cli_create_issue(jira, ai_provider, default_prompt, template_dir, args):
    try:
        template = TemplateLoader(template_dir, args.type)
        fields = template.get_fields()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise (FileNotFoundError(e))

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
        raise (AiError(msg))

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
        raise (CreateIssueError)
