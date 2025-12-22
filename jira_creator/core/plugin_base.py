#!/usr/bin/env python
"""
Base plugin class for jira-creator commands.

This module provides the abstract base class that all command plugins
must inherit from. It defines the interface for registering arguments,
executing commands, and performing REST operations.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional, Type

from jira_creator.core.plugin_config import DisplayConfig, FieldMapping, ValidationRule


class JiraPlugin(ABC):
    """
    Abstract base class for all Jira command plugins.

    Each plugin encapsulates both the CLI command logic and the corresponding
    REST API operation, reducing duplication and improving testability.
    """

    def __init__(self, **kwargs):
        """
        Initialize the plugin with optional dependency injection.

        Arguments:
            **kwargs: Optional dependencies for testing (e.g., ai_provider, editor_func)
        """
        # Store injected dependencies for testing
        self._injected_deps = kwargs

    @property
    @abstractmethod
    def command_name(self) -> str:
        """
        Return the CLI command name.

        Returns:
            str: The command name as it appears in the CLI (e.g., 'add-comment')
        """

    @property
    @abstractmethod
    def help_text(self) -> str:
        """
        Return help text for the command.

        Returns:
            str: Brief description of what the command does
        """

    @property
    def example_commands(self) -> List[str]:
        """
        Return example command invocations.

        Plugins can override this to provide helpful usage examples.

        Returns:
            List[str]: Example command strings (without program name prefix)
        """
        return []

    @property
    def category(self) -> str:
        """
        Return the category this command belongs to for help organization.

        Plugins can override this to specify their category. Default is "Other".

        Returns:
            str: Category name (e.g., "Issue Creation & Management")
        """
        return "Other"

    @abstractmethod
    def register_arguments(self, parser: ArgumentParser) -> None:
        """
        Register command-specific arguments with the argument parser.

        Arguments:
            parser: ArgumentParser instance to add arguments to
        """

    @abstractmethod
    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the command logic.

        This method handles the CLI interaction, argument processing,
        and delegates to rest_operation for the actual API call.

        Arguments:
            client: JiraClient instance for making API calls
            args: Parsed command-line arguments

        Returns:
            bool: True if successful, False otherwise

        Raises:
            Various exceptions based on the specific command implementation
        """

    @abstractmethod
    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation.

        This method contains the core REST logic, separated from CLI concerns
        for better testability and reusability.

        Arguments:
            client: JiraClient instance for making API calls
            **kwargs: Operation-specific parameters

        Returns:
            Dict[str, Any]: API response data

        Raises:
            Various exceptions based on the specific operation
        """

    def set_dependency(self, dep_name: str, value: Any) -> None:
        """
        Set an injected dependency.

        This method allows runtime dependency injection, useful for
        providing services like plugin_registry to plugins that need it.

        Arguments:
            dep_name: Name of the dependency
            value: The dependency value to inject
        """
        self._injected_deps[dep_name] = value

    def get_dependency(self, dep_name: str, default: Optional[Any] = None) -> Any:
        """
        Get an injected dependency or its default value.

        This method supports dependency injection for testing while
        providing sensible defaults for production use.

        Arguments:
            dep_name: Name of the dependency
            default: Default value/factory if dependency not injected

        Returns:
            The injected dependency or default value
        """
        if dep_name in self._injected_deps:
            return self._injected_deps[dep_name]

        # Call default if it's a callable (factory function)
        if callable(default):
            return default()

        return default

    def get_fix_capabilities(self) -> List[Dict[str, Any]]:
        """
        Register fix capabilities that this plugin can perform.

        Plugins can override this method to register automated fix methods
        that can be invoked by AI-powered tools (e.g., lint-all --ai-fix).

        Returns:
            List of fix capability dicts, each containing:
            - method_name: str - unique identifier for this fix method
            - description: str - what this fix does
            - params: Dict[str, str] - parameter names and types
            - conditions: Optional[Dict] - when this fix applies

        Example:
            [
                {
                    "method_name": "set_priority",
                    "description": "Set the priority of an issue",
                    "params": {
                        "issue_key": "str",
                        "priority": "str (Critical/High/Medium/Low/Normal)"
                    },
                    "conditions": {
                        "problem_patterns": ["Priority not set", "priority"],
                        "required_status": ["In Progress", "New"]
                    }
                }
            ]
        """
        return []  # Default: no fix capabilities

    def execute_fix(self, client: Any, method_name: str, args: Dict[str, Any]) -> bool:
        """
        Execute a specific fix method.

        Plugins that register fix capabilities must override this method
        to handle execution of their registered fix methods.

        Arguments:
            client: JiraClient instance
            method_name: The fix method to execute
            args: Arguments for the fix method

        Returns:
            bool: True if fix succeeded, False otherwise

        Raises:
            NotImplementedError: If plugin doesn't implement fix execution
        """
        raise NotImplementedError(f"Plugin {self.command_name} does not implement execute_fix for {method_name}")

    def get_plugin_exceptions(self) -> Dict[str, Type[Exception]]:
        """
        Register exceptions that this plugin defines.

        Plugins can override this method to register their custom exceptions
        with the registry for centralized discovery and documentation.

        Returns:
            Dict mapping exception names to exception classes

        Example:
            {
                "CreateIssueError": CreateIssueError,
                "TemplateNotFoundError": TemplateNotFoundError,
            }
        """
        return {}  # Default: no plugin-specific exceptions

    def get_ai_prompts(self) -> Dict[str, str]:
        """
        Register AI prompts that this plugin uses.

        Plugins can override this method to provide custom AI prompts for
        text generation, issue creation, or other AI-assisted operations.

        Returns:
            Dict mapping prompt names to prompt text

        Example:
            {
                "task_description": "As a professional Principal Software Engineer...",
                "story_description": "Write user stories with strong focus...",
                "generate_acceptance_criteria": "Create clear acceptance criteria...",
            }
        """
        return {}  # Default: no plugin-specific prompts

    def get_field_mappings(self) -> Dict[str, FieldMapping]:
        """
        Register JIRA field mappings that this plugin uses.

        Plugins can override this method to declare which JIRA fields they
        need, along with environment variable mappings and defaults.

        Returns:
            Dict mapping logical field names to FieldMapping configurations

        Example:
            {
                "epic": FieldMapping(
                    env_var="JIRA_EPIC_FIELD",
                    default="customfield_12311140",
                    required=False,
                    description="Epic link field for linking stories to epics"
                ),
                "story_points": FieldMapping(
                    env_var="JIRA_STORY_POINTS_FIELD",
                    default="customfield_12310243",
                    required=True,
                    description="Story points estimation field"
                )
            }
        """
        return {}  # Default: no field mappings

    def get_display_config(self) -> Optional[DisplayConfig]:
        """
        Define how this plugin displays issue data.

        Plugins that display issues (like list, search) can override this
        to customize the display format, columns, and sorting.

        Returns:
            DisplayConfig with display preferences, or None for default

        Example:
            DisplayConfig(
                columns=["key", "summary", "status", "assignee"],
                sort_by="updated",
                sort_order="desc",
                truncate_summary=True,
                format="table"
            )
        """
        return None  # Default: use system defaults

    def get_validation_rules(self) -> List[ValidationRule]:
        """
        Register validation rules for issue fields.

        Plugins can override this method to define validation rules
        that will be applied to issue data.

        Returns:
            List of ValidationRule objects

        Example:
            [
                ValidationRule(
                    field="summary",
                    required=True,
                    min_length=10,
                    error_message="Summary must be at least 10 characters"
                ),
                ValidationRule(
                    field="description",
                    required=True,
                    validator=lambda v: v and len(v.strip()) > 0,
                    error_message="Description cannot be empty"
                )
            ]
        """
        return []  # Default: no validation rules

    def before_execute(self, client: Any, args: Namespace) -> None:  # pylint: disable=unused-argument
        """
        Hook called before execute() is invoked.

        Plugins can override this for setup, validation, or logging
        before the main execution logic runs.

        Arguments:
            client: JiraClient instance
            args: Parsed command-line arguments

        Raises:
            Any exception will prevent execute() from running
        """
        pass  # pylint: disable=unnecessary-pass

    def after_execute(self, client: Any, args: Namespace, result: Any) -> None:  # pylint: disable=unused-argument
        """
        Hook called after execute() completes successfully.

        Plugins can override this for cleanup, logging, or post-processing
        after the main execution logic completes.

        Arguments:
            client: JiraClient instance
            args: Parsed command-line arguments
            result: Return value from execute()
        """
        pass  # pylint: disable=unnecessary-pass

    def on_error(self, client: Any, args: Namespace, error: Exception) -> None:  # pylint: disable=unused-argument
        """
        Hook called if execute() raises an exception.

        Plugins can override this for custom error handling, logging,
        or cleanup when execution fails.

        Arguments:
            client: JiraClient instance
            args: Parsed command-line arguments
            error: The exception that was raised

        Note:
            This is called before the exception is re-raised
        """
        pass  # pylint: disable=unnecessary-pass
