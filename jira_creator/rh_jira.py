#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from jira.client import JiraClient
from jira.jira_prompts import JiraIssueType, JiraPromptLibrary
from providers import get_ai_provider
from templates.template_loader import TemplateLoader


class JiraCLI:
    def __init__(self):
        self.template_dir = Path(
            os.getenv(
                "TEMPLATE_DIR", os.path.join(os.path.dirname(__file__) + "/templates")
            )
        )
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

        list_issues = add("list", "List assigned issues")
        list_issues.add_argument("--project")
        list_issues.add_argument("--component")
        list_issues.add_argument("--user")
        list_issues.add_argument(
            "--blocked", action="store_true", help="Show only blocked issues"
        )
        list_issues.add_argument(
            "--unblocked", action="store_true", help="Show only unblocked issues"
        )
        list_issues.add_argument("--status", help="Filter by JIRA status")
        list_issues.add_argument("--summary", help="Filter by summary text")
        list_issues.add_argument(
            "--show-reason",
            action="store_true",
            help="Show blocked reason field in listing",
        )

        search = add("search", "Search issues via JQL")
        search.add_argument("jql", help="JIRA Query Language expression")

        change_type = add("change", "Change issue type")
        change_type.add_argument("issue_key")
        change_type.add_argument("new_type")

        migrate = add("migrate", "Migrate issue to a new type")
        migrate.add_argument("issue_key")
        migrate.add_argument("new_type")

        edit = add("edit", "Edit an issue's description")
        edit.add_argument("issue_key")
        edit.add_argument("--no-ai", action="store_true")

        set_priority = add("set-priority", "Set issue priority")
        set_priority.add_argument("issue_key")
        set_priority.add_argument("priority")

        set_status = add("set-status", "Set issue status")
        set_status.add_argument("issue_key")
        set_status.add_argument("status")

        add_sprint = add("add-sprint", "Add issue to sprint by name")
        add_sprint.add_argument("issue_key")
        add_sprint.add_argument("sprint_name")

        remove_sprint = add("remove-sprint", "Remove issue from its sprint")
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

        set_points = add("set-story-points", "Set story points directly")
        set_points.add_argument("issue_key")
        set_points.add_argument("points", help="Story point estimate (integer)")

        block = add("block", "Mark an issue as blocked")
        block.add_argument("issue_key")
        block.add_argument("reason", help="Reason the issue is blocked")

        unblock = add("unblock", "Mark an issue as unblocked")
        unblock.add_argument("issue_key")

        blocked = add("blocked", "List blocked issues")
        blocked.add_argument("--user", help="Filter by assignee (username)")
        blocked.add_argument("--project", help="Optional project key")
        blocked.add_argument("--component", help="Optional component")

        lint = add("lint", "Lint an issue for quality")
        lint.add_argument("issue_key")

        lint_all = add("lint-all", "Lint all issues assigned to you")
        lint_all.add_argument("--project", help="Project key override")
        lint_all.add_argument("--component", help="Component filter")

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

    def set_story_points(self, args):
        try:
            points = int(args.points)
        except ValueError:
            print("❌ Points must be an integer.")
            return

        try:
            self.jira.set_story_points(args.issue_key, points)
            print(f"✅ Set {points} story points on {args.issue_key}")
        except Exception as e:
            print(f"❌ Failed to set story points: {e}")

    def block(self, args):
        try:
            self.jira.block_issue(args.issue_key, args.reason)
            print(f"✅ {args.issue_key} marked as blocked: {args.reason}")
        except Exception as e:
            print(f"❌ Failed to mark {args.issue_key} as blocked: {e}")

    def unblock(self, args):
        try:
            self.jira.unblock_issue(args.issue_key)
            print(f"✅ {args.issue_key} marked as unblocked")
        except Exception as e:
            print(f"❌ Failed to unblock {args.issue_key}: {e}")

    def lint(self, args):
        try:
            issue = self.jira._request("GET", f"/rest/api/2/issue/{args.issue_key}")
            fields = issue["fields"]

            problems = []

            if not fields.get("summary"):
                problems.append("❌ Missing summary")
            if not fields.get("description"):
                problems.append("❌ Missing description")
            if not fields.get("priority"):
                problems.append("❌ Priority not set")
            if fields.get("customfield_12310243") in [None, ""]:
                problems.append("❌ Story points not assigned")

            if fields.get("customfield_12316543", {}).get("value") == "True":
                reason = fields.get("customfield_12316544")
                if not reason:
                    problems.append("❌ Issue is blocked but has no blocked reason")

            if fields.get("status", {}).get("name") == "In Progress" and not fields.get(
                "assignee"
            ):
                problems.append("❌ Issue is In Progress but unassigned")

            if problems:
                print(f"⚠️ Lint issues found in {args.issue_key}:")
                for p in problems:
                    print(f" - {p}")
            else:
                print(f"✅ {args.issue_key} passed all lint checks")

        except Exception as e:
            print(f"❌ Failed to lint issue {args.issue_key}: {e}")

    def lint_all(self, args):
        try:
            issues = self.jira.list_issues(args.project, args.component)

            if not issues:
                print("✅ No issues assigned to you.")
                return

            failures = {}

            for issue in issues:
                key = issue["key"]
                full_issue = self.jira._request("GET", f"/rest/api/2/issue/{key}")
                fields = full_issue["fields"]
                problems = []

                if not fields.get("summary"):
                    problems.append("❌ Missing summary")
                if not fields.get("description"):
                    problems.append("❌ Missing description")
                if not fields.get("priority"):
                    problems.append("❌ Priority not set")
                if fields.get("customfield_12310243") in [None, ""]:
                    problems.append("❌ Story points not assigned")
                if fields.get("customfield_12316543", {}).get("value") == "True":
                    reason = fields.get("customfield_12316544")
                    if not reason:
                        problems.append("❌ Issue is blocked but has no blocked reason")
                if fields.get("status", {}).get(
                    "name"
                ) == "In Progress" and not fields.get("assignee"):
                    problems.append("❌ Issue is In Progress but unassigned")

                if problems:
                    failures[key] = problems

            if not failures:
                print("✅ All issues passed lint checks!")
            else:
                print("⚠️ Issues with lint problems:")
                for key, problems in failures.items():
                    print(f"\n🔍 {key}")
                    for p in problems:
                        print(f" - {p}")

        except Exception as e:
            print(f"❌ Failed to lint issues: {e}")

    def blocked(self, args):
        try:
            issues = self.jira.list_issues(
                project=args.project,
                component=args.component,
                user=args.user or self.jira.get_current_user(),
            )

            if not issues:
                print("✅ No issues found.")
                return

            blocked_issues = []
            for issue in issues:
                fields = issue["fields"]
                is_blocked = (
                    fields.get("customfield_12316543", {}).get("value") == "True"
                )
                if is_blocked:
                    blocked_issues.append(
                        {
                            "key": issue["key"],
                            "status": fields["status"]["name"],
                            "assignee": (
                                fields["assignee"]["displayName"]
                                if fields["assignee"]
                                else "Unassigned"
                            ),
                            "reason": fields.get("customfield_12316544", "(no reason)"),
                            "summary": fields["summary"],
                        }
                    )

            if not blocked_issues:
                print("✅ No blocked issues found.")
                return

            print("🔒 Blocked issues:")
            print("-" * 80)
            for i in blocked_issues:
                print(f"{i['key']} [{i['status']}] — {i['assignee']}")
                print(f"  🔸 Reason: {i['reason']}")
                print(f"  📄 {i['summary']}")
                print("-" * 80)

        except Exception as e:
            print(f"❌ Failed to list blocked issues: {e}")


if __name__ == "__main__":
    JiraCLI().run()
