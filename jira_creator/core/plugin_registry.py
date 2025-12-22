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

from .plugin_base import JiraPlugin


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
        self._exceptions: Dict[str, type[Exception]] = {}
        self._ai_prompts: Dict[str, Dict[str, str]] = {}  # plugin_name -> {prompt_name -> prompt_text}
        self._field_mappings: Dict[str, Dict[str, any]] = {}  # plugin_name -> {field_name -> FieldMapping}

    def discover_plugins(self, plugin_dir: Optional[str] = None) -> None:  # pylint: disable=too-many-locals
        """
        Automatically discover and load all plugins from the plugin directory.

        Arguments:
            plugin_dir: Directory to search for plugins (default: plugins/)
        """
        if plugin_dir is None:
            # Get the plugins directory (sibling to core/)
            current_dir = Path(__file__).parent
            plugin_dir_path = current_dir.parent / "plugins"
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

                        # Register plugin exceptions  # pragma: no cover
                        plugin_exceptions = plugin_instance.get_plugin_exceptions()  # pragma: no cover
                        for exc_name, exc_class in plugin_exceptions.items():  # pragma: no cover
                            self._exceptions[exc_name] = exc_class  # pragma: no cover

                        # Register plugin AI prompts  # pragma: no cover
                        plugin_prompts = plugin_instance.get_ai_prompts()  # pragma: no cover
                        if plugin_prompts:  # pragma: no cover
                            self._ai_prompts[command_name] = plugin_prompts  # pragma: no cover

                        # Register plugin field mappings  # pragma: no cover
                        field_mappings = plugin_instance.get_field_mappings()  # pragma: no cover
                        if field_mappings:  # pragma: no cover
                            self._field_mappings[command_name] = field_mappings  # pragma: no cover

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

    def get_all_plugin_names(self) -> List[str]:
        """
        Get list of all registered plugin names.

        This is an alias for list_plugins() for compatibility with AIExecutor.

        Returns:
            List of plugin command names
        """
        return self.list_plugins()

    def register_all(self, subparsers) -> None:
        """
        Register all discovered plugins with the argument parser.

        Arguments:
            subparsers: Subparser object from ArgumentParser
        """
        for command_name, plugin in self._plugins.items():
            parser = subparsers.add_parser(command_name, help=plugin.help_text)
            plugin.register_arguments(parser)

    def get_exception(self, name: str) -> Optional[type[Exception]]:
        """
        Get a registered exception class by name.

        Arguments:
            name: The exception class name to look up

        Returns:
            Exception class or None if not found
        """
        return self._exceptions.get(name)

    def list_exceptions(self) -> Dict[str, type[Exception]]:
        """
        Get all registered plugin exceptions.

        Returns:
            Dict mapping exception names to exception classes
        """
        return self._exceptions.copy()

    def get_all_exceptions(self) -> Dict[str, type[Exception]]:
        """
        Get all registered plugin exceptions.

        This is an alias for list_exceptions() for consistency with other API methods.

        Returns:
            Dict mapping exception names to exception classes
        """
        return self.list_exceptions()

    def get_ai_prompts(self, plugin_name: str) -> Dict[str, str]:
        """
        Get AI prompts registered by a specific plugin.

        Arguments:
            plugin_name: The command name of the plugin

        Returns:
            Dict mapping prompt names to prompt text
        """
        return self._ai_prompts.get(plugin_name, {})

    def get_all_ai_prompts(self) -> Dict[str, Dict[str, str]]:
        """
        Get all AI prompts from all plugins.

        Returns:
            Dict mapping plugin names to their prompt dictionaries
        """
        return self._ai_prompts.copy()

    def get_field_mappings(self, plugin_name: str) -> Dict[str, any]:
        """
        Get field mappings registered by a specific plugin.

        Arguments:
            plugin_name: The command name of the plugin

        Returns:
            Dict mapping field names to FieldMapping objects
        """
        return self._field_mappings.get(plugin_name, {})

    def get_all_field_mappings(self) -> Dict[str, Dict[str, any]]:
        """
        Get all field mappings from all plugins.

        Returns:
            Dict mapping plugin names to their field mapping dictionaries
        """
        return self._field_mappings.copy()

    def clear(self) -> None:
        """Clear all registered plugins, exceptions, prompts, and field mappings."""
        self._plugins.clear()
        self._plugin_classes.clear()
        self._exceptions.clear()
        self._ai_prompts.clear()
        self._field_mappings.clear()

    def reload_plugin_from_file(self, file_path: str) -> bool:
        """
        Reload a plugin from a modified file.

        This method reloads the Python module and re-instantiates the plugin,
        useful after AI-powered auto-fixes modify plugin code.

        Arguments:
            file_path: Absolute path to the plugin file that was modified

        Returns:
            True if plugin was successfully reloaded, False otherwise
        """
        import sys

        # Convert file path to module name
        # e.g., /path/to/jira_creator/plugins/create_issue_plugin.py -> jira_creator.plugins.create_issue_plugin
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or not file_path_obj.name.endswith("_plugin.py"):
            return False

        module_name = f"jira_creator.plugins.{file_path_obj.stem}"

        try:
            # Reload the module if it's already loaded
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            # Find and re-register all plugin classes from this module
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, JiraPlugin) and cls != JiraPlugin and not inspect.isabstract(cls):
                    # Re-instantiate the plugin
                    plugin_instance = cls()
                    command_name = plugin_instance.command_name

                    # Update the registry with new instance and class
                    self._plugins[command_name] = plugin_instance
                    self._plugin_classes[command_name] = cls

                    # Re-register plugin exceptions
                    plugin_exceptions = plugin_instance.get_plugin_exceptions()
                    for exc_name, exc_class in plugin_exceptions.items():
                        self._exceptions[exc_name] = exc_class

                    # Re-register plugin AI prompts
                    plugin_prompts = plugin_instance.get_ai_prompts()
                    if plugin_prompts:
                        self._ai_prompts[command_name] = plugin_prompts

                    # Re-register plugin field mappings
                    field_mappings = plugin_instance.get_field_mappings()
                    if field_mappings:
                        self._field_mappings[command_name] = field_mappings

            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Warning: Failed to reload plugin {file_path_obj.name}: {e}")
            return False
