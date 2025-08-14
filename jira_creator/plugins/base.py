#!/usr/bin/env python
"""
Base plugin class for jira-creator commands.

This module provides the abstract base class that all command plugins
must inherit from. It defines the interface for registering arguments,
executing commands, and performing REST operations.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, Optional


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
