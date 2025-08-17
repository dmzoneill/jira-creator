#!/usr/bin/env python
"""
Plugin registry for dynamic plugin discovery and management.

This module provides the PluginRegistry class that handles automatic
discovery, loading, and registration of command plugins.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import JiraPlugin


class PluginRegistry:
    """
    Registry for dynamically loading and managing Jira command plugins.

    This class handles the discovery, loading, and registration of plugins,
    providing a clean interface for the main CLI to interact with commands.
    """

    def __init__(self):
        """Initialize an empty plugin registry."""
        self._plugins: Dict[str, JiraPlugin] = {}
        self._plugin_classes: Dict[str, Type[JiraPlugin]] = {}

    def discover_plugins(self, plugin_dir: Optional[str] = None) -> None:
        """
        Automatically discover and load all plugins from the plugin directory.

        Arguments:
            plugin_dir: Directory to search for plugins (default: plugins/)
        """
        if plugin_dir is None:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            plugin_dir_path = current_dir
        else:
            plugin_dir_path = Path(plugin_dir)

        # Find all Python files ending with _plugin.py
        for file_path in plugin_dir_path.glob("*_plugin.py"):
            if file_path.name.startswith("_"):
                continue  # Skip private modules

            try:
                # Import the module
                module_name = f"jira_creator.plugins.{file_path.stem}"
                module = importlib.import_module(module_name)

                # Find all classes that inherit from JiraPlugin
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if (  # pragma: no cover
                        issubclass(cls, JiraPlugin)  # pragma: no cover
                        and cls != JiraPlugin  # pragma: no cover
                        and not inspect.isabstract(cls)  # pragma: no cover
                    ):  # pragma: no cover
                        # Store the class for later instantiation  # pragma: no cover
                        plugin_instance = cls()  # pragma: no cover
                        command_name = plugin_instance.command_name  # pragma: no cover
                        self._plugins[command_name] = plugin_instance  # pragma: no cover
                        self._plugin_classes[command_name] = cls  # pragma: no cover

            except Exception as e:  # pylint: disable=broad-exception-caught
                # Log error but continue loading other plugins
                print(f"Warning: Failed to load plugin {file_path.name}: {e}")

    def get_plugin(self, command: str) -> Optional[JiraPlugin]:
        """
        Get a plugin instance by command name.

        Arguments:
            command: The command name to look up

        Returns:
            JiraPlugin instance or None if not found
        """
        # Convert underscores to hyphens for command lookup
        command = command.replace("_", "-")
        return self._plugins.get(command)

    def get_plugin_class(self, command: str) -> Optional[Type[JiraPlugin]]:
        """
        Get a plugin class by command name.

        Arguments:
            command: The command name to look up

        Returns:
            JiraPlugin class or None if not found
        """
        command = command.replace("_", "-")
        return self._plugin_classes.get(command)

    def create_plugin(self, command: str, **kwargs) -> Optional[JiraPlugin]:
        """
        Create a new plugin instance with dependency injection.

        Arguments:
            command: The command name
            **kwargs: Dependencies to inject

        Returns:
            New JiraPlugin instance or None if not found
        """
        plugin_class = self.get_plugin_class(command)
        if plugin_class:
            return plugin_class(**kwargs)
        return None

    def list_plugins(self) -> List[str]:
        """
        Get a list of all registered plugin command names.

        Returns:
            List of command names
        """
        return sorted(self._plugins.keys())

    def register_all(self, subparsers) -> None:
        """
        Register all discovered plugins with the argument parser.

        Arguments:
            subparsers: Subparser object from ArgumentParser
        """
        for command_name, plugin in self._plugins.items():
            parser = subparsers.add_parser(command_name, help=plugin.help_text)
            plugin.register_arguments(parser)

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()
        self._plugin_classes.clear()
