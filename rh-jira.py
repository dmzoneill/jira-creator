#!/usr/bin/python
import os
import sys
import json
from pathlib import Path
import tempfile
import subprocess

from providers import get_ai_provider
from templates.template_loader import TemplateLoader
from jira.client import JiraClient

TEMPLATE_DIR = Path(os.getenv("TEMPLATE_DIR", "./templates"))

# --- CLI Args ---
dry_run = "--dry-run" in sys.argv
edit_mode = "--edit" in sys.argv

for flag in ("--dry-run", "--edit"):
    if flag in sys.argv:
        sys.argv.remove(flag)

if len(sys.argv) < 3:
    print('Usage: python rh-jira.py <issue_type> "Issue Summary" [--dry-run] [--edit]')
    sys.exit(1)

issue_type = sys.argv[1].lower()
summary = sys.argv[2]

# --- Load Template ---
try:
    template_loader = TemplateLoader(TEMPLATE_DIR, issue_type)
    fields = template_loader.get_fields()
except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1)

# --- Prompt for Fields ---
user_inputs = {}

if edit_mode:
    # Pre-fill fields as commented placeholders
    for field in fields:
        user_inputs[field] = f"# {field}"

    raw_description = template_loader.render_description(user_inputs)

    # Open editor
    editor = os.environ.get("EDITOR", "vim")
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".tmp", delete=False) as tmpfile:
        tmpfile.write(raw_description)
        tmpfile.flush()
        subprocess.call([editor, tmpfile.name])
        tmpfile.seek(0)
        description = tmpfile.read()
else:
    for field in fields:
        user_inputs[field] = input(f"{field}: ")
    description = template_loader.render_description(user_inputs)

# --- Clean up with AI ---
ai_provider = get_ai_provider(os.getenv("AI_PROVIDER", "openai"))
prompt = (
    "Keep the format and headings of this text, just fix spelling errors, grammatical issues, "
    "and improve the readability of sentences by providing more clarity."
)

try:
    description = ai_provider.improve_text(prompt, description)
except Exception as e:
    print(f"Warning: AI provider failed to clean up text. Using original. Error: {e}")

# --- Build and Submit ---
jira = JiraClient()
payload = jira.build_payload(summary, description, issue_type)

if dry_run:
    print("\n📦 DRY RUN ENABLED")
    print("---- Description ----")
    print(description)
    print("---- Payload ----")
    print(json.dumps(payload, indent=2))
    sys.exit(0)

try:
    issue_key = jira.create_issue(payload)
    print(f"✅ Issue created: {jira.jira_url}/browse/{issue_key}")
except Exception as e:
    print(f"❌ Failed to create issue: {e}")
