#!/usr/bin/env python
"""
Base plugin class for jira-creator commands.

This module provides the abstract base class that all command plugins
must inherit from. It defines the interface for registering arguments,
executing commands, and performing REST operations.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional


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
