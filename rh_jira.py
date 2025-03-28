#!/usr/bin/env python3
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

from providers import get_ai_provider
from templates.template_loader import TemplateLoader
from jira.client import JiraClient
from jira_prompts import JiraPromptLibrary, JiraIssueType


class JiraCLI:
    def __init__(self):
        self.template_dir = Path(os.getenv("TEMPLATE_DIR", "./templates"))
        self.jira = JiraClient()
        self.ai_provider = get_ai_provider(os.getenv("AI_PROVIDER", "openai"))
        self.default_prompt = (
            "As a professional Principal Software Engineer, you write acute, well-defined Jira issues "
            "with a strong focus on clear descriptions, definitions of done, acceptance criteria, and supporting details. "
            "If standard Jira sections are missing, add them. Improve clarity, fix grammar and spelling, and maintain structure."
        )

    def run(self):
        import argparse
        import argcomplete

        prog_name = os.environ.get("CLI_NAME", os.path.basename(sys.argv[0]))

        parser = argparse.ArgumentParser(description="JIRA Issue Tool", prog=prog_name)

        subparsers = parser.add_subparsers(dest="command", required=True)

        # Create
        create_parser = subparsers.add_parser("create", help="Create a new issue")
        create_parser.add_argument("type", help="Issue type (bug, story, epic, etc.)")
        create_parser.add_argument("summary", help="Issue summary")
        create_parser.add_argument(
            "--edit", action="store_true", help="Use $EDITOR to fill in fields"
        )
        create_parser.add_argument(
            "--dry-run", action="store_true", help="Print payload without sending"
        )

        # Change Type
        change_parser = subparsers.add_parser("change-type", help="Change issue type")
        change_parser.add_argument("issue_key")
        change_parser.add_argument("new_type")

        # Migrate
        migrate_parser = subparsers.add_parser(
            "migrate-to", help="Migrate issue to a new type"
        )
        migrate_parser.add_argument("new_type")
        migrate_parser.add_argument("issue_key")

        # Edit Issue
        edit_parser = subparsers.add_parser(
            "edit-issue", help="Edit an existing issue's description"
        )
        edit_parser.add_argument("issue_key")
        edit_parser.add_argument("--no-ai", action="store_true", help="Skip AI cleanup")

        argcomplete.autocomplete(parser)
        args = parser.parse_args()

        if args.command == "change-type":
            self.change_type(args.issue_key, args.new_type)
        elif args.command == "migrate-to":
            self.migrate_issue(args.issue_key, args.new_type)
        elif args.command == "create":
            self.create_issue(args.type, args.summary, args.edit, args.dry_run)
        elif args.command == "edit-issue":
            self.edit_issue(args.issue_key, no_ai=args.no_ai)

    def create_issue(self, issue_type, summary, edit_mode, dry_run):
        try:
            template_loader = TemplateLoader(self.template_dir, issue_type)
            fields = template_loader.get_fields()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)

        user_inputs = {}

        if edit_mode:
            for field in fields:
                user_inputs[field] = f"# {field}"

            raw_description = template_loader.render_description(user_inputs)
            editor = os.environ.get("EDITOR", "vim")
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".tmp", delete=False
            ) as tmpfile:
                tmpfile.write(raw_description)
                tmpfile.flush()
                subprocess.call([editor, tmpfile.name])
                tmpfile.seek(0)
                description = tmpfile.read()
        else:
            for field in fields:
                user_inputs[field] = input(f"{field}: ")
            description = template_loader.render_description(user_inputs)

        # Choose prompt based on issue type
        try:
            enum_type = JiraIssueType(issue_type.lower())
            prompt = JiraPromptLibrary.get_prompt(enum_type)
        except ValueError:
            print(
                f"⚠️ Warning: Unknown issue type '{issue_type}'. Using default prompt."
            )
            prompt = self.default_prompt

        try:
            description = self.ai_provider.improve_text(prompt, description)
        except Exception as e:
            print(
                f"Warning: AI provider failed to clean up text. Using original. Error: {e}"
            )

        payload = self.jira.build_payload(summary, description, issue_type)

        if dry_run:
            print("📦 DRY RUN ENABLED")
            print("---- Description ----")
            print(description)
            print("---- Payload ----")
            print(json.dumps(payload, indent=2))
            return

        try:
            issue_key = self.jira.create_issue(payload)
            print(f"✅ Issue created: {self.jira.jira_url}/browse/{issue_key}")
        except Exception as e:
            print(f"❌ Failed to create issue: {e}")

    def change_type(self, issue_key, new_type):
        try:
            success = self.jira.change_issue_type(issue_key, new_type)
            if success:
                print(f"✅ Changed issue {issue_key} to type '{new_type}'")
            else:
                print(f"❌ Failed to change issue {issue_key}")
        except Exception as e:
            print(f"❌ Error changing issue type: {e}")

    def migrate_issue(self, old_key, new_type):
        try:
            new_key = self.jira.migrate_issue(old_key, new_type)
            print(
                f"✅ Migrated {old_key} to {new_type.upper()} → {self.jira.jira_url}/browse/{new_key}"
            )
        except Exception as e:
            print(f"❌ Failed to migrate issue: {e}")

    def edit_issue(self, issue_key, no_ai=False):
        try:
            original = self.jira.get_description(issue_key)
        except Exception as e:
            print(f"❌ Failed to fetch description: {e}")
            return

        # Open in editor
        editor = os.environ.get("EDITOR", "vim")
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".md", delete=False
        ) as tmpfile:
            tmpfile.write(original or "")
            tmpfile.flush()
            subprocess.call([editor, tmpfile.name])
            tmpfile.seek(0)
            edited = tmpfile.read()

        # Choose prompt dynamically
        try:
            issue_type = self.jira.get_issue_type(issue_key)
            enum_type = JiraIssueType(issue_type.lower())
            prompt = JiraPromptLibrary.get_prompt(enum_type)
        except Exception:
            prompt = self.default_prompt

        if not no_ai:
            try:
                cleaned = self.ai_provider.improve_text(prompt, edited)
            except Exception as e:
                print(f"⚠️ AI cleanup failed, using raw edited version. Error: {e}")
                cleaned = edited
        else:
            cleaned = edited

        try:
            self.jira.update_description(issue_key, cleaned)
            print(f"✅ Description updated for {issue_key}")
        except Exception as e:
            print(f"❌ Failed to update issue: {e}")


if __name__ == "__main__":
    JiraCLI().run()
