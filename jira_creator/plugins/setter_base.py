#!/usr/bin/env python
"""
Base class for simple setter plugins.

This module provides a generic base class for commands that follow
the pattern of setting a single field value on a Jira issue.
"""

from abc import abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.plugins.base import JiraPlugin


class SetterPlugin(JiraPlugin):
    """
    Generic base class for setter commands.

    This handles the common pattern of commands that set a single
    field value on a Jira issue.
    """

    @property
    @abstractmethod
    def field_name(self) -> str:
        """Return the human-readable field name (e.g., 'priority', 'status')."""

    @property
    @abstractmethod
    def argument_name(self) -> str:
        """Return the CLI argument name for the value to set."""

    @property
    def argument_help(self) -> str:
        """Return help text for the value argument."""
        return f"The {self.field_name} to set"

    @property
    def command_name(self) -> str:
        """Return the command name based on field name."""
        return f"set-{self.field_name.lower().replace(' ', '-')}"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return f"Set the {self.field_name} of a Jira issue"

    def get_exception_class(self):
        """Get the appropriate exception class for this setter."""
        # Import here to avoid circular imports
        from jira_creator.exceptions.exceptions import (
            SetComponentError,
            SetPriorityError,
            SetProjectError,
            SetStatusError,
            SetSummaryError,
            SetWorkstreamError,
        )

        exception_map = {
            "priority": SetPriorityError,
            "status": SetStatusError,
            "summary": SetSummaryError,
            "component": SetComponentError,
            "project": SetProjectError,
            "workstream": SetWorkstreamError,
        }

        # Default to generic Exception if specific one not found
        return exception_map.get(self.field_name.lower(), Exception)

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument(self.argument_name, help=self.argument_help)
        # Allow subclasses to add more arguments
        self.register_additional_arguments(parser)

    def register_additional_arguments(self, parser: ArgumentParser) -> None:
        """Override to add additional arguments in subclasses."""

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the setter command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        exception_class = self.get_exception_class()

        try:
            # Get the value to set from args
            value = getattr(args, self.argument_name)

            # Perform the REST operation
            self.rest_operation(
                client,
                issue_key=args.issue_key,
                value=value,
                args=args,  # Pass full args for subclasses that need more
            )

            # Format success message
            success_msg = self.format_success_message(args.issue_key, value)
            print(success_msg)
            return True

        except exception_class as e:
            msg = f"❌ Failed to set {self.field_name}: {e}"
            print(msg)
            raise exception_class(e) from e

    def format_success_message(self, issue_key: str, value: Any) -> str:
        """Format the success message. Override for custom formatting."""
        return f"✅ {self.field_name.capitalize()} for {issue_key} set to '{value}'"

    @abstractmethod
    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation.

        Subclasses must implement this to perform the actual API call.
        kwargs will contain 'issue_key', 'value', and 'args'.
        """
