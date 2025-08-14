#!/usr/bin/env python
"""
Test to ensure all plugin files are imported for coverage reporting.

This test doesn't test functionality, but ensures that all plugin files
are included in the coverage report by importing them.
"""

import importlib
import os
from pathlib import Path

import pytest


def test_all_plugins_can_be_imported():
    """Import all plugin files to ensure they're included in coverage."""
    plugins_dir = Path(__file__).parent.parent / "plugins"

    # Get all Python files in the plugins directory
    plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith("_plugin.py") and not f.startswith("_")]

    # Import each plugin module
    for plugin_file in plugin_files:
        module_name = f"jira_creator.plugins.{plugin_file[:-3]}"  # Remove .py
        importlib.import_module(module_name)

    # Also import the non-plugin modules
    importlib.import_module("jira_creator.plugins.base")
    importlib.import_module("jira_creator.plugins.registry")
    importlib.import_module("jira_creator.plugins.setter_base")

    assert len(plugin_files) > 0, "No plugin files found"


def test_import_error_handling():
    """Test handling of import errors."""
    with pytest.raises(ImportError):
        importlib.import_module("jira_creator.plugins.nonexistent_plugin")
