#!/usr/bin/env python
"""
Test to ensure all plugin files are imported for coverage reporting.

This test doesn't test functionality, but ensures that all plugin files
are included in the coverage report by importing them.
"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path

import pytest


def _load_plugin_module(plugins_dir: Path, plugin_file: str):
    """Load a plugin file after confirming it stays under the plugins directory."""
    resolved = (plugins_dir / plugin_file).resolve()
    if not resolved.is_relative_to(plugins_dir.resolve()):
        raise ImportError(f"plugin path escapes plugins directory: {plugin_file}")
    if not plugin_file.endswith("_plugin.py") or not resolved.stem.isidentifier():
        raise ImportError(f"invalid plugin module name: {plugin_file}")
    module_name = f"jira_creator.plugins.{resolved.stem}"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load plugin {plugin_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_all_plugins_can_be_imported():
    """Import all plugin files to ensure they're included in coverage."""
    plugins_dir = Path(__file__).parent.parent / "plugins"

    # Get all Python files in the plugins directory
    plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith("_plugin.py") and not f.startswith("_")]

    # Import each plugin module
    for plugin_file in plugin_files:
        _load_plugin_module(plugins_dir, plugin_file)

    # Also import the core modules
    importlib.import_module("jira_creator.core.plugin_base")
    importlib.import_module("jira_creator.core.plugin_registry")
    importlib.import_module("jira_creator.core.plugin_setter_base")

    assert len(plugin_files) > 0, "No plugin files found"


def test_import_error_handling():
    """Test handling of import errors."""
    with pytest.raises(ImportError):
        importlib.import_module("jira_creator.plugins.nonexistent_plugin")
