import json
import os
import subprocess
import sys
import tempfile

from jira.jira_prompts import JiraIssueType, JiraPromptLibrary
from templates.template_loader import TemplateLoader


def handle(jira, ai_provider, default_prompt, template_dir, args):
    try:
        template = TemplateLoader(template_dir, args.type)
        fields = template.get_fields()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    inputs = (
        {field: input(f"{field}: ") for field in fields}
        if not args.edit
        else {field: f"# {field}" for field in fields}
    )

    description = template.render_description(inputs)
    print("DEBUG: Rendered description BEFORE AI:")
    print(description)

    if args.edit:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".tmp", delete=False) as tmp:
            tmp.write(description)
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            description = tmp.read()

    try:
        enum_type = JiraIssueType(args.type.lower())
        prompt = JiraPromptLibrary.get_prompt(enum_type)
    except ValueError:
        print(f"⚠️ Unknown issue type '{args.type}'. Using default prompt.")
        prompt = default_prompt

    try:
        description = ai_provider.improve_text(prompt, description)
    except Exception as e:
        print(f"⚠️ AI cleanup failed. Using original text. Error: {e}")

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
    except Exception as e:
        print(f"❌ Failed to create issue: {e}")
