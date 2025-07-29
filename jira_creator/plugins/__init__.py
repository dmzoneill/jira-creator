#!/usr/bin/env python
"""
Plugin infrastructure for jira-creator.

This module provides the base classes and registry for implementing
commands as plugins, reducing code duplication and improving testability.
"""

from .base import JiraPlugin
from .registry import PluginRegistry

__all__ = ["JiraPlugin", "PluginRegistry"]
