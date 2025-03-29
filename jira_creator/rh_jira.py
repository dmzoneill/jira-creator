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
from jira.jira_prompts import JiraPromptLibrary, JiraIssueType


class JiraCLI:
    def __init__(self):
        self.template_dir = Path(os.getenv("TEMPLATE_DIR", os.path.join(os.path.dirname(__file__) + "/templates")))
        self.jira = JiraClient()
        self.ai_provider = get_ai_provider(os.getenv("AI_PROVIDER", "openai"))
        self.default_prompt = JiraPromptLibrary.get_prompt("default")
        self.comment_prompt = JiraPromptLibrary.get_prompt("comment")

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
        def add(name, help_text, aliases=None):
            return subparsers.add_parser(name, help=help_text, aliases=aliases or [])

        create = add("create", "Create a new issue")
        create.add_argument("type")
        create.add_argument("summary")
        create.add_argument("--edit", action="store_true")
        create.add_argument("--dry-run", action="store_true")

        list_issues = add("list", "List assigned issues", aliases=["ls"])
        list_issues.add_argument("--project")
        list_issues.add_argument("--component")
        list_issues.add_argument("--user")

        change_type = add("change", "Change issue type")
        change_type.add_argument("issue_key")
        change_type.add_argument("new_type")

        migrate = add("migrate", "Migrate issue to a new type")
        migrate.add_argument("issue_key")
        migrate.add_argument("new_type")

        edit = add("edit", "Edit an issue's description")
        edit.add_argument("issue_key")
        edit.add_argument("--no-ai", action="store_true")

        set_priority = add("set-priority", "Set issue priority", aliases=["priority"])
        set_priority.add_argument("issue_key")
        set_priority.add_argument("priority")

        set_status = add("set-status", "Set issue status", aliases=["status"])
        set_status.add_argument("issue_key")
        set_status.add_argument("status")

        add_sprint = add(
            "add-sprint", "Add issue to sprint by name", aliases=["sprint-add"]
        )
        add_sprint.add_argument("issue_key")
        add_sprint.add_argument("sprint_name")

        remove_sprint = add(
            "remove-sprint", "Remove issue from its sprint", aliases=["sprint-remove"]
        )
        remove_sprint.add_argument("issue_key")

        unassign = add("unassign", "Unassign a user from an issue")
        unassign.add_argument("issue_key")

        comment = add("add-comment", "Add a comment to an issue")
        comment.add_argument("issue_key")
        comment.add_argument(
            "--text", help="Comment text (optional, otherwise opens $EDITOR)"
        )

        vote = add("vote-story-points", "Vote on story points")
        vote.add_argument("issue_key")
        vote.add_argument("points", help="Story point estimate (integer)")

    def _dispatch_command(self, args):
        try:
            getattr(self, args.command.replace("-", "_"))(args)
        except Exception as e:
            print(f"❌ Command failed: {e}")

    def add_comment(self, args):
        if args.text:
            comment = args.text
        else:
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".md", delete=False
            ) as tmp:
                tmp.write("# Enter comment below\n")
                tmp.flush()
                subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
                tmp.seek(0)
                comment = tmp.read()

        if not comment.strip():
            print("⚠️ No comment provided. Skipping.")
            return

        try:
            cleaned = self.ai_provider.improve_text(self.default_prompt, comment)
        except Exception as e:
            print(f"⚠️ AI cleanup failed. Using raw comment. Error: {e}")
            cleaned = comment

        try:
            self.jira.add_comment(args.issue_key, cleaned)
            print(f"✅ Comment added to {args.issue_key}")
        except Exception as e:
            print(f"❌ Failed to add comment: {e}")

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

    def list(self, args):
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

    def migrate(self, args):
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

    def vote_story_points(self, args):
        try:
            points = int(args.points)
        except ValueError:
            print("❌ Points must be an integer.")
            return

        try:
            self.jira.vote_story_points(args.issue_key, points)
            print(f"✅ Voted {points} points on {args.issue_key}")
        except Exception as e:
            print(f"❌ Failed to vote on story points: {e}")


if __name__ == "__main__":
    JiraCLI().run()
