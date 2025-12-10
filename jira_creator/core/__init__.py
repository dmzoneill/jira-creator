#!/usr/bin/env python
"""
Core infrastructure for jira-creator.

This module provides the base classes and registry for the plugin system.
"""

from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_registry import PluginRegistry
from jira_creator.core.plugin_setter_base import SetterPlugin

__all__ = ["JiraPlugin", "PluginRegistry", "SetterPlugin"]
