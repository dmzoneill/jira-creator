#!/usr/bin/env python
"""
Plugin infrastructure for jira-creator.

This module provides the base classes and registry for implementing
commands as plugins, reducing code duplication and improving testability.
"""

from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_registry import PluginRegistry

__all__ = ["JiraPlugin", "PluginRegistry"]
