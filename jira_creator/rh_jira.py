#!/usr/bin/env python3
"""
A command-line interface (CLI) tool for managing JIRA issues.

This script provides a set of commands to interact with JIRA, allowing users to create, edit, and manage issues, as
well as perform various operations such as assigning users, adding comments, and managing sprints. It integrates with
AI services to assist with issue creation and management.

Key Features:
- Create, edit, and delete JIRA issues.
- Assign and unassign users to/from issues.
- Add comments and manage issue statuses.
- Search for issues using JIRA Query Language (JQL).
- Integrate AI assistance for issue handling and suggestions.
- Lint issues for quality checks and provide feedback.
- Manage sprints and track progress.

Dependencies:
- core.env_fetcher: For fetching environment variables.
- exceptions.exceptions: Custom exceptions for error handling.
- providers: For obtaining AI provider instances.
- rest.client: JIRA client for making API requests.
- rest.prompts: For handling prompt templates used in AI interactions.

Usage:
Run the script from the command line, providing appropriate subcommands and arguments based on the desired action.
"""
# pylint: disable=import-outside-toplevel, too-many-locals, too-many-statements, too-many-public-methods
import os
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import DispatcherError
from providers import get_ai_provider
from rest.client import JiraClient
from rest.prompts import IssueType, PromptLibrary

from commands import (  # isort: skip
    _try_cleanup,
    cli_add_comment,
    cli_add_to_sprint,
    cli_ai_helper,
    cli_assign,
    cli_block,
    cli_blocked,
    cli_change_type,
    cli_create_issue,
    cli_edit_issue,
    cli_lint,
    cli_lint_all,
    cli_list_issues,
    cli_open_issue,
    cli_migrate,
    cli_remove_sprint,
    cli_quarterly_connection,
    cli_search,
    cli_search_users,
    cli_set_acceptance_criteria,
    cli_set_priority,
    cli_set_status,
    cli_set_story_epic,
    cli_set_story_points,
    cli_talk,
    cli_unassign,
    cli_unblock,
    cli_validate_issue,
    cli_view_issue,
    cli_view_user,
    cli_vote_story_points,
    cli_add_flag,
    cli_remove_flag,
    cli_list_sprints,
    cli_set_summary,
    cli_clone_issue,
    cli_get_sprint,
    # commands entry
)


class JiraCLI:
    """
    A command-line interface (CLI) for interacting with JIRA issues, enabling users to manage issues, perform
    AI-assisted operations, and execute various JIRA-related tasks.

    Attributes:
    - jira (JiraClient): An instance of the JiraClient used to interact with the JIRA API.
    - template_dir (Path): The directory path for templates fetched from the environment.
    - ai_provider: The AI provider instance configured based on environment variables.
    - default_prompt: The default prompt for AI interactions.
    - comment_prompt: The prompt used for adding comments to issues.
    - ai_helper_prompt: The prompt used for AI helper functionalities.
    """

    def __init__(self) -> None:
        """
        Initializes the JiraBot object with required variables and settings.

        Arguments:
        None

        Side Effects:
        - Initializes a JiraClient object and assigns it to self.jira.
        - Fetches required environment variables using EnvFetcher.
        - Sets the template directory path based on the value retrieved from the environment variables.
        - Retrieves and sets the AI provider based on the value retrieved from the environment variables.
        - Sets default prompts for different issue types using PromptLibrary.

        Returns:
        None
        """

        self.jira: JiraClient = JiraClient()
        required_vars: list[str] = [
            "JPAT",
            "AI_PROVIDER",
            "AI_MODEL",
            "AI_URL",
            "JIRA_URL",
            "PROJECT_KEY",
            "AFFECTS_VERSION",
            "COMPONENT_NAME",
            "PRIORITY",
            "AI_API_KEY",
            "JIRA_BOARD_ID",
            "JIRA_EPIC_FIELD",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD",
            "JIRA_BLOCKED_FIELD",
            "JIRA_BLOCKED_REASON_FIELD",
            "JIRA_STORY_POINTS_FIELD",
            "JIRA_SPRINT_FIELD",
            "JIRA_VIEW_COLUMNS",
        ]

        EnvFetcher.fetch_all(required_vars)
        self.template_dir: Path = Path(EnvFetcher.get("TEMPLATE_DIR"))
        self.ai_provider = get_ai_provider(EnvFetcher.get("AI_PROVIDER"))
        self.default_prompt = PromptLibrary.get_prompt(IssueType["DEFAULT"])
        self.comment_prompt = PromptLibrary.get_prompt(IssueType["COMMENT"])
        self.ai_helper_prompt = PromptLibrary.get_prompt(IssueType["AIHELPER"])

    def run(self) -> None:
        """
        Initialize the argcomplete module for command-line argument completion.

        Arguments:
        - self: The instance of the class.

        Exceptions:
        None
        """

        import argcomplete

        prog_name: str = os.environ.get("CLI_NAME", os.path.basename(sys.argv[0]))
        parser: ArgumentParser = ArgumentParser(
            description="JIRA Issue Tool", prog=prog_name
        )
        subparsers: _SubParsersAction = parser.add_subparsers(
            dest="command", required=True
        )

        self._register_subcommands(subparsers)
        argcomplete.autocomplete(parser)
        args: Namespace = parser.parse_args()
        self._dispatch_command(args)

    def _register_subcommands(self, subparsers: _SubParsersAction) -> None:
        """
        Registers subcommands for a given argparse subparsers object.

        Arguments:
        - subparsers (_SubParsersAction): An instance of the argparse subparsers object to which subcommands will be
        registered.

        Side Effects:
        Modifies the subparsers object by registering subcommands for it.
        """

        def add(name, help_text, aliases=None):
            """
            Creates a new subparser for command-line argument parsing.

            Args:
            name (str): The name of the subparser.
            help_text (str): The help text displayed when using the subparser.
            aliases (list, optional): A list of alternative names for the subparser. Defaults to None.

            Returns:
            argparse.ArgumentParser: The newly created subparser.
            """

            return subparsers.add_parser(name, help=help_text, aliases=aliases or [])

        # --- 🧠 AI Helper ---
        ai_helper = add("ai-helper", "AI Helper")
        ai_helper.add_argument("prompt", help="A string describing a series of actions")
        ai_helper.add_argument("--voice", action="store_true")

        # --- 📌 Issue Creation & Editing ---
        create = add("create-issue", "Create a new issue")
        create.add_argument("type", help="bug, story, epic, task, spike")
        create.add_argument("summary", help="title of the issue")
        create.add_argument("--edit", action="store_true")
        create.add_argument("--dry-run", action="store_true")
        create.add_argument(
            "--lint",
            action="store_true",
            help="Run interactive linting on the description after AI cleanup",
        )

        edit = add("edit-issue", "Edit an issue's description")
        edit.add_argument("issue_key", help="The Jira issue id/key")
        edit.add_argument("--no-ai", action="store_true")
        edit.add_argument(
            "--lint",
            action="store_true",
            help="Run interactive linting on the description after AI cleanup",
        )

        # --- 🧾 Issue Metadata ---
        set_priority = add("set-priority", "Set issue priority")
        set_priority.add_argument("issue_key", help="The Jira issue id/key")
        set_priority.add_argument("priority", help="normal, major, critical")

        set_story_epic = add("set-story-epic", "Set stories epic")
        set_story_epic.add_argument("issue_key", help="The Jira issue id/key")
        set_story_epic.add_argument("epic_key", help="The Jira epic key")

        set_status = add("set-status", "Set issue status")
        set_status.add_argument("issue_key", help="The Jira issue id/key")
        set_status.add_argument("status", help="Closed, In Progress, Refinement, New")

        set_acceptance_criteria = add(
            "set-acceptance-criteria", "Set issue acceptance criteria"
        )
        set_acceptance_criteria.add_argument("issue_key", help="The Jira issue id/key")
        set_acceptance_criteria.add_argument(
            "acceptance_criteria", help="What needs to be done to accept it as complete"
        )

        change_type = add("change", "Change issue type")
        change_type.add_argument("issue_key", help="The Jira issue id/key")
        change_type.add_argument("new_type", help="bug, story, epic, task, spike")

        migrate = add("migrate", "Migrate issue to a new type")
        migrate.add_argument("issue_key", help="The Jira issue id/key")
        migrate.add_argument("new_type", help="bug, story, epic, task, spike")

        # --- 👤 Assignment & Workflow ---
        assign = add("assign", "Assign a user to an issue")
        assign.add_argument("issue_key", help="The Jira issue id/key")
        assign.add_argument("assignee", help="The person to assign it to")

        unassign = add("unassign", "Unassign a user from an issue")
        unassign.add_argument("issue_key", help="The Jira issue id/key")

        block = add("block", "Mark an issue as blocked")
        block.add_argument("issue_key", help="The Jira issue id/key")
        block.add_argument("reason", help="Reason the issue is blocked")

        unblock = add("unblock", "Mark an issue as unblocked")
        unblock.add_argument("issue_key", help="The Jira issue id/key")

        # --- 🧠 Estimation ---
        vote = add("vote-story-points", "Vote on story points")
        vote.add_argument("issue_key", help="The Jira issue id/key")
        vote.add_argument("points", help="Story point estimate (integer)")

        set_points = add("set-story-points", "Set story points directly")
        set_points.add_argument("issue_key", help="The Jira issue id/key")
        set_points.add_argument("points", help="Story point estimate (integer)")

        # --- 📅 Sprints ---
        add_to_sprint = add("add-to-sprint", "Add issue to sprint by name")
        add_to_sprint.add_argument("issue_key", help="The Jira issue id/key")
        add_to_sprint.add_argument("sprint_name", help="The name of the sprint")
        add_to_sprint.add_argument(
            "--assignee", help="Assign it to a specific user (default to current user)"
        )

        remove_sprint = add("remove-sprint", "Remove issue from its sprint")
        remove_sprint.add_argument("issue_key", help="The Jira issue id/key")

        # --- 💬 Comments ---
        comment = add("add-comment", "Add a comment to an issue")
        comment.add_argument("issue_key", help="The Jira issue id/key")
        comment.add_argument(
            "--text", help="Comment text (optional, otherwise opens $EDITOR)"
        )

        # --- 🔍 Issue Lookup ---
        search = add("search", "Search issues via JQL")
        search.add_argument("jql", help="JIRA Query Language expression")

        # --- 🔍 List issues ---
        list_issues = add("list-issues", "List assigned issues")
        list_issues.add_argument("--project")
        list_issues.add_argument("--component")
        list_issues.add_argument("--assignee", help="Filter by JIRA issues by user")
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
        list_issues.add_argument("--reporter", help="Filter by JIRA issues by user")
        list_issues.add_argument("--columns", help="The columns to show")
        list_issues.add_argument("--sort", help="Sort the output by these columns")

        lint = add("lint", "Lint an issue for quality")
        lint.add_argument("issue_key", help="The Jira issue id/key")

        lint_all = add("lint-all", "Lint all issues assigned to you")
        lint_all.add_argument("--project", help="Project key override")
        lint_all.add_argument("--component", help="Component filter")
        lint_all.add_argument("--assignee", help="Assignee filter")
        lint_all.add_argument("--reporter", help="Reporter filter")

        # --- 🔍 Viewers ---
        open_issue = add("open-issue", "Open issue in the browser")
        open_issue.add_argument("issue_key", help="The Jira issue id/key")

        view_issue = add("view-issue", "View issue in the console")
        view_issue.add_argument("issue_key", help="The Jira issue id/key")

        view_user = add("view-user", "Get and display a user")
        view_user.add_argument("account_id", help="Jira account ID")

        search_users = add("search-users", "Search for users by term")
        search_users.add_argument("query", help="Search term")

        blocked = add("blocked", "List blocked issues")
        blocked.add_argument("--user", help="Filter by assignee (username)")
        blocked.add_argument("--project", help="Optional project key")
        blocked.add_argument("--component", help="Optional component")

        # talk to jira
        talk = add("talk", "Talk to jira")
        talk.add_argument("--voice", action="store_true")

        # --- 📊 Reporting ---
        add("quarterly-connection", "Perform a quarterly connection report")

        add_flag = add("add-flag", "Add a flag to a specific issue")
        add_flag.add_argument("issue_key", help="The key of the issue")

        remove_flag = add("remove-flag", "Remove a flag from a specific issue")
        remove_flag.add_argument("issue_key", help="The key of the issue")

        add("list-sprints", "List current and future sprints")

        set_summary = add("set-summary", "Sets the summary on a specific issue")
        set_summary.add_argument("issue_key", help="The key of the issue")
        set_summary.add_argument("summary", help="The name of the flag to add")

        clone_issue = add("clone-issue", "Clone an issue")
        clone_issue.add_argument("issue_key", help="The key of the issue")

        add("get-sprint", "Add a flag to a specific issue")

        # Add your other subcommands here

    def _dispatch_command(self, args: Namespace) -> None:
        """
        Dispatches a command based on the input arguments.

        Arguments:
        - self: The instance of the class.
        - args (Namespace): A namespace containing the command to be executed.

        Exceptions:
        - DispatcherError: Raised when the command execution fails.

        Side Effects:
        - Prints an error message if the command execution fails.
        """

        try:
            getattr(self, args.command.replace("-", "_"))(args)
        except AttributeError as e:
            msg: str = f"❌ Command failed: {e}"
            print(msg)
            raise DispatcherError(e) from e

    def ai_helper(self, args: Namespace) -> None:
        """
        Execute the AI helper functionality with the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed for the AI helper functionality.

        Side Effects:
        - Executes the CLI AI helper function with the current object instance, AI provider, AI helper prompt, and the
        provided arguments.
        """

        return cli_ai_helper(self, self.ai_provider, self.ai_helper_prompt, args)

    def open_issue(self, args: Namespace) -> None:
        """
        Open an issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed to open an issue.

        Side Effects:
        - Calls the cli_open_issue function with the provided arguments.
        """

        return cli_open_issue(self.jira, args)

    def view_issue(self, args: Namespace) -> None:
        """
        View an issue in Jira using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed to view the issue in Jira.

        Side Effects:
        - Calls the cli_view_issue function with the Jira object and the provided arguments.
        """

        return cli_view_issue(self.jira, args)

    def add_comment(self, args: Namespace) -> None:
        """
        Adds a comment to a Jira issue using the provided arguments.

        Arguments:
        - self: The instance of the class.
        - args (Namespace): A Namespace object containing the necessary arguments for adding a comment to a Jira issue.

        Side Effects:
        - Modifies the Jira issue by adding a comment.
        """

        return cli_add_comment(self.jira, self.ai_provider, self.comment_prompt, args)

    def create_issue(self, args: Namespace) -> None:
        """
        Creates an issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing arguments for creating the issue.

        Side Effects:
        - Calls the cli_create_issue function with the necessary parameters to create an issue.
        """

        return cli_create_issue(self.jira, self.ai_provider, self.template_dir, args)

    def list_issues(self, args: Namespace) -> None:
        """
        Calls a CLI function to list issues based on the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing parsed arguments.

        Return:
        None
        """

        return cli_list_issues(self.jira, args)

    def change_type(self, args: Namespace) -> None:
        """
        Change the type of an issue in Jira using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed to change the type of the issue in Jira.

        Side Effects:
        - Modifies the type of the specified issue in Jira.
        """

        return cli_change_type(self.jira, args)

    def migrate(self, args: Namespace) -> None:
        """
        Migrates data using the provided arguments.

        Arguments:
        - self: The object itself.
        - args (Namespace): A Namespace object containing parsed command-line arguments.

        Side Effects:
        - Calls the cli_migrate function with the Jira instance and the provided arguments.
        """

        return cli_migrate(self.jira, args)

    def edit_issue(self, args: Namespace) -> None:
        """
        Edit an issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A namespace object containing the arguments needed for editing the issue.

        Side Effects:
        - Modifies the state of the issue in Jira based on the provided arguments.
        """

        return cli_edit_issue(
            self.jira, self.ai_provider, self.default_prompt, _try_cleanup, args
        )

    def _try_cleanup(self, prompt: str, text: str) -> str:
        """
        Attempts to clean up the given text using the AI provider.

        Args:
        prompt (str): The prompt to be used for cleaning up the text.
        text (str): The text to be cleaned up.

        Returns:
        str: The cleaned-up text after processing with the AI provider.
        """

        return _try_cleanup(self.ai_provider, prompt, text)

    def unassign(self, args: Namespace) -> None:
        """
        Unassigns an issue in Jira.

        Arguments:
        - self: the object instance
        - args (Namespace): A Namespace object containing the arguments needed to unassign the issue.

        Side Effects:
        - Modifies the assignment of the specified Jira issue.
        """

        return cli_unassign(self.jira, args)

    def assign(self, args: Namespace) -> None:
        """
        Assign an issue in Jira to a user.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing command-line arguments.

        Exceptions:
        - None

        Side Effects:
        - Modifies the assignment of an issue in Jira.

        Return:
        - None
        """

        return cli_assign(self.jira, args)

    def set_priority(self, args: Namespace) -> None:
        """
        Set the priority of a Jira issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed to set the priority.

        Return:
        - None

        Exceptions:
        - No exceptions are raised explicitly within this function.
        """

        return cli_set_priority(self.jira, args)

    def set_story_epic(self, args: Namespace) -> None:
        """
        Set the epic for a story in Jira.

        Arguments:
        - self: the object instance
        - args (Namespace): A namespace containing the arguments for setting the epic of a story in Jira.

        Exceptions:
        - None

        Side Effects:
        - Modifies the epic of a story in Jira.
        """

        return cli_set_story_epic(self.jira, args)

    def remove_sprint(self, args: Namespace) -> None:
        """
        Remove a sprint from Jira board.

        Arguments:
        - self: the instance of the class.
        - args (Namespace): A Namespace object containing parsed arguments from the command line.

        Exceptions:
        - None

        Side Effects:
        - Modifies the Jira board by removing a sprint.
        """

        return cli_remove_sprint(self.jira, args)

    def add_to_sprint(self, args: Namespace) -> None:
        """
        Adds a sprint to a Jira board using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the necessary arguments for adding a sprint.

        Exceptions:
        - None
        """

        return cli_add_to_sprint(self.jira, args)

    def set_status(self, args: Namespace) -> None:
        """
        Set the status of an issue in Jira using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A namespace containing the arguments needed to set the status of an issue in Jira.

        Exceptions:
        - None

        Side Effects:
        - Modifies the status of an issue in Jira.

        Return:
        - None
        """

        return cli_set_status(self.jira, args)

    def set_acceptance_criteria(self, args: Namespace) -> None:
        """
        Set acceptance criteria for a Jira issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the command-line arguments.

        Exceptions:
        None

        Side Effects:
        Calls the cli_set_acceptance_criteria function with the Jira instance and the provided arguments.

        Return:
        None
        """

        return cli_set_acceptance_criteria(self.jira, args)

    def vote_story_points(self, args: Namespace) -> None:
        """
        Cast a vote for story points on a Jira issue.

        Arguments:
        - self: The current instance of the class.
        - args (Namespace): A namespace object containing parsed command-line arguments.

        Side Effects:
        - Calls the 'cli_vote_story_points' function with the Jira instance and provided arguments.
        """

        return cli_vote_story_points(self.jira, args)

    def set_story_points(self, args: Namespace) -> None:
        """
        Set the story points for a Jira issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed to set story points for a Jira issue.

        Exceptions:
        - None

        Side Effects:
        - Calls the cli_set_story_points function with the Jira instance and provided arguments.

        Return:
        - None
        """

        return cli_set_story_points(self.jira, args)

    def block(self, args: Namespace) -> None:
        """
        Execute a blocking operation using arguments provided in the Namespace object.

        Arguments:
        - self: the instance of the class containing the method.
        - args (Namespace): Namespace object containing arguments for the operation.

        Side Effects:
        - Executes a blocking operation using the provided arguments.
        """

        return cli_block(self.jira, args)

    def unblock(self, args: Namespace) -> None:
        """
        Unblocks an item in Jira using the provided arguments.

        Arguments:
        - self: the instance of the class.
        - args (Namespace): Namespace object containing the arguments needed to unblock the item in Jira.

        Side Effects:
        - Modifies the state of the item in Jira by unblocking it.
        """

        return cli_unblock(self.jira, args)

    def validate_issue(self, fields: dict[str, str]) -> None:
        """
        Validates the provided fields for an issue using a CLI validation function.

        Arguments:
        - fields (dict[str, str]): A dictionary containing the fields of the issue to be validated.
        - self (implicit): Instance of the class containing the method.

        Returns:
        - None
        """

        return cli_validate_issue(fields, self.ai_provider)

    def lint(self, args: Namespace) -> None:
        """
        Lint the provided arguments using the CLI linter.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the parsed arguments.

        Side Effects:
        - Calls the cli_lint function with the provided Jira instance, AI provider, and parsed arguments.
        """

        return cli_lint(self.jira, self.ai_provider, args)

    def lint_all(self, args: Namespace) -> None:
        """
        Lint all Jira issues using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing parsed command-line arguments.

        Side Effects:
        - Calls cli_lint_all function with Jira instance, AI provider instance, and parsed arguments.
        """

        return cli_lint_all(self.jira, self.ai_provider, args)

    def blocked(self, args: Namespace) -> None:
        """
        Calls a function to block a specific resource using Jira.

        Arguments:
        - self: the instance of the class
        - args (Namespace): A Namespace object containing the arguments passed to the function.

        Exceptions:
        - None
        """

        return cli_blocked(self.jira, args)

    def search(self, args: Namespace) -> None:
        """
        Search for items using the Jira API based on the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A namespace object containing the search parameters.

        Side Effects:
        - Calls the 'cli_search' function with the Jira instance and provided arguments.
        """

        return cli_search(self.jira, args)

    def quarterly_connection(self, _: Namespace) -> None:
        """
        Execute a quarterly connection using the provided arguments.

        Arguments:
        - self: the object instance
        - _: A Namespace object containing the arguments for the connection

        Side Effects:
        - Calls cli_quarterly_connection function with the Jira and AI provider attributes of the object instance
        """

        return cli_quarterly_connection(self.jira, self.ai_provider)

    def search_users(self, args: Namespace) -> None:
        """
        Searches for users using the provided arguments.

        Arguments:
        - self: the object instance
        - args (Namespace): A Namespace object containing the arguments for the search.

        Side Effects:
        Calls the 'cli_search_users' function with the 'jira' attribute and the provided arguments.
        """

        return cli_search_users(self.jira, args)

    def talk(self, args: Namespace) -> None:
        """
        Executes the 'cli_talk' function with the provided arguments.

        Arguments:
        - self: The instance of the class.
        - args (Namespace): A Namespace object containing the command-line arguments.

        Side Effects:
        - Calls the 'cli_talk' function with the provided arguments.
        """

        return cli_talk(self, args)

    def view_user(self, args: Namespace) -> None:
        """
        View a user's information using the CLI.

        Arguments:
        - self: the object instance
        - args (Namespace): A Namespace object containing parsed arguments from the command line.

        Exceptions: None
        """

        return cli_view_user(self.jira, args)

    def add_flag(self, args: Namespace) -> None:
        """
        Adds a flag to a Jira issue using the provided arguments.

        Arguments:
        - self: the object instance
        - args (Namespace): Namespace object containing parsed command-line arguments

        Exceptions:
        - No exceptions are raised by this function.

        Side Effects:
        - Modifies the Jira issue by adding a flag.

        Return:
        - None
        """

        return cli_add_flag(self.jira, args)

    def remove_flag(self, args: Namespace) -> None:
        """
        Remove a flag from a Jira issue.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing parsed arguments.

        Exceptions:
        - No exceptions are raised by this function.

        Side Effects:
        - Modifies the Jira issue by removing a flag.
        """

        return cli_remove_flag(self.jira, args)

    def list_sprints(self, args: Namespace) -> None:
        """
        List sprints using the provided Jira instance and command-line arguments.

        Arguments:
        - self: The instance of the class containing the method.
        - args (Namespace): A namespace object containing command-line arguments.

        Return:
        None
        """

        return cli_list_sprints(self.jira, args)

    def set_summary(self, args: Namespace) -> None:
        """
        Set a summary for a Jira issue using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A Namespace object containing the arguments needed to set the summary for a Jira issue.

        Exceptions:
        None

        Side Effects:
        Calls an external function cli_set_summary() to set the summary for a Jira issue.

        Return:
        None
        """

        return cli_set_summary(self.jira, args)

    def clone_issue(self, args: Namespace) -> None:
        """
        Clones an issue in Jira using the provided arguments.

        Arguments:
        - self: The object instance.
        - args (Namespace): A namespace object containing the arguments needed for cloning the issue.

        Side Effects:
        - Clones the specified issue in Jira.
        """

        return cli_clone_issue(self.jira, args)

    def get_sprint(self, args: Namespace) -> None:
        """
        Get the current sprint.

        Arguments:
        - self: the object instance
        - args (Namespace): Namespace object containing arguments

        Return:
        - None
        """
        return cli_get_sprint(self.jira, args)

    # add new df here


if __name__ == "__main__":  # pragma: no cover
    JiraCLI().run()  # pragma: no cover
