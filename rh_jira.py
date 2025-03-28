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

        self._register_subcommands(subparsers)
        argcomplete.autocomplete(parser)
        args = parser.parse_args()
        self._dispatch_command(args)

    def _register_subcommands(self, subparsers):
        def add(*args, **kwargs):
            return subparsers.add_parser(*args, **kwargs)

        create = add("create", help="Create a new issue")
        create.add_argument("type")
        create.add_argument("summary")
        create.add_argument("--edit", action="store_true")
        create.add_argument("--dry-run", action="store_true")

        list_issues = add("list-issues", help="List assigned issues")
        list_issues.add_argument("--project")
        list_issues.add_argument("--component")
        list_issues.add_argument("--user")

        change_type = add("change-type", help="Change issue type")
        change_type.add_argument("issue_key")
        change_type.add_argument("new_type")

        unassign = add("unassign", help="Unassign a user from an issue")
        unassign.add_argument("issue_key")

        migrate = add("migrate-to", help="Migrate issue to a new type")
        migrate.add_argument("new_type")
        migrate.add_argument("issue_key")

        edit = add("edit-issue", help="Edit an issue's description")
        edit.add_argument("issue_key")
        edit.add_argument("--no-ai", action="store_true")

        priority = add("set-priority", help="Set issue priority")
        priority.add_argument("issue_key")
        priority.add_argument("priority")

        sprint = add("set-sprint", help="Set sprint by ID")
        sprint.add_argument("issue_key")
        sprint.add_argument("sprint_id")

        remove = add("remove-sprint", help="Remove from sprint")
        remove.add_argument("issue_key")

        add_sprint = add("add-sprint", help="Add to sprint by name")
        add_sprint.add_argument("issue_key")
        add_sprint.add_argument("sprint_name")

        status = add("set-status", help="Set issue status")
        status.add_argument("issue_key")
        status.add_argument("status")

    def _dispatch_command(self, args):
        try:
            getattr(self, args.command.replace("-", "_"))(args)
        except Exception as e:
            print(f"❌ Command failed: {e}")

    def create(self, args):
        try:
            template = TemplateLoader(self.template_dir, args.type)
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

        if args.edit:
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".tmp", delete=False
            ) as tmp:
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
            prompt = self.default_prompt

        try:
            description = self.ai_provider.improve_text(prompt, description)
        except Exception as e:
            print(f"⚠️ AI cleanup failed. Using original text. Error: {e}")

        payload = self.jira.build_payload(args.summary, description, args.type)

        if args.dry_run:
            print("📦 DRY RUN ENABLED")
            print("---- Description ----")
            print(description)
            print("---- Payload ----")
            print(json.dumps(payload, indent=2))
            return

        try:
            key = self.jira.create_issue(payload)
            print(f"✅ Created: {self.jira.jira_url}/browse/{key}")
        except Exception as e:
            print(f"❌ Failed to create issue: {e}")

    def list_issues(self, args):
        try:
            issues = self.jira.list_issues(args.project, args.component, args.user)
            if not issues:
                print("No issues found.")
                return

            rows = []
            for issue in issues:
                f = issue["fields"]
                sprints = f.get("customfield_12310940") or []
                sprint = next(
                    (
                        s.split("=")[1]
                        for s in sprints
                        if "state=ACTIVE" in s and "name=" in s
                    ),
                    "—",
                )
                rows.append(
                    (
                        issue["key"],
                        f["status"]["name"],
                        f["assignee"]["displayName"] if f["assignee"] else "Unassigned",
                        f.get("priority", {}).get("name", "—"),
                        str(f.get("customfield_12310243", "—")),
                        sprint,
                        f["summary"],
                    )
                )

            rows.sort(key=lambda r: (r[5], r[1]))
            headers = [
                "Key",
                "Status",
                "Assignee",
                "Priority",
                "Points",
                "Sprint",
                "Summary",
            ]
            widths = [
                max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
            ]
            header_fmt = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
            print(header_fmt)
            print("-" * len(header_fmt))
            for r in rows:
                print(" | ".join(val.ljust(widths[i]) for i, val in enumerate(r)))
        except Exception as e:
            print(f"❌ Failed to list issues: {e}")

    def change_type(self, args):
        try:
            if self.jira.change_issue_type(args.issue_key, args.new_type):
                print(f"✅ Changed {args.issue_key} to '{args.new_type}'")
            else:
                print(f"❌ Change failed for {args.issue_key}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def migrate_to(self, args):
        try:
            new_key = self.jira.migrate_issue(args.issue_key, args.new_type)
            print(
                f"✅ Migrated {args.issue_key} to {new_key}: {self.jira.jira_url}/browse/{new_key}"
            )
        except Exception as e:
            print(f"❌ Migration failed: {e}")

    def edit_issue(self, args):
        try:
            original = self.jira.get_description(args.issue_key)
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".md", delete=False
            ) as tmp:
                tmp.write(original or "")
                tmp.flush()
                subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
                tmp.seek(0)
                edited = tmp.read()
        except Exception as e:
            print(f"❌ Failed to fetch/edit: {e}")
            return

        try:
            prompt = JiraPromptLibrary.get_prompt(
                JiraIssueType(self.jira.get_issue_type(args.issue_key).lower())
            )
        except Exception:
            prompt = self.default_prompt

        cleaned = edited if args.no_ai else self._try_cleanup(prompt, edited)
        try:
            self.jira.update_description(args.issue_key, cleaned)
            print(f"✅ Updated {args.issue_key}")
        except Exception as e:
            print(f"❌ Update failed: {e}")

    def _try_cleanup(self, prompt, text):
        try:
            return self.ai_provider.improve_text(prompt, text)
        except Exception as e:
            print(f"⚠️ AI cleanup failed: {e}")
            return text

    def unassign(self, args):
        success = self.jira.unassign_issue(args.issue_key)
        print(
            f"✅ Unassigned {args.issue_key}"
            if success
            else f"❌ Could not unassign {args.issue_key}"
        )

    def set_priority(self, args):
        try:
            self.jira.set_priority(args.issue_key, args.priority)
            print(f"✅ Priority set to '{args.priority}'")
        except Exception as e:
            print(f"❌ Failed to set priority: {e}")

    def set_sprint(self, args):
        try:
            sid = int(args.sprint_id) if args.sprint_id.isdigit() else None
            self.jira.set_sprint(args.issue_key, sid)
            print(f"✅ Sprint updated for {args.issue_key}")
        except Exception as e:
            print(f"❌ Failed to set sprint: {e}")

    def remove_sprint(self, args):
        try:
            self.jira.remove_from_sprint(args.issue_key)
            print("✅ Removed from sprint")
        except Exception as e:
            print(f"❌ Failed to remove sprint: {e}")

    def add_sprint(self, args):
        try:
            self.jira.add_to_sprint_by_name(args.issue_key, args.sprint_name)
            print(f"✅ Added to sprint '{args.sprint_name}'")
        except Exception as e:
            print(f"❌ {e}")

    def set_status(self, args):
        try:
            self.jira.set_status(args.issue_key, args.status)
            print(f"✅ Status set to '{args.status}'")
        except Exception as e:
            print(f"❌ Failed to update status: {e}")


if __name__ == "__main__":
    JiraCLI().run()
