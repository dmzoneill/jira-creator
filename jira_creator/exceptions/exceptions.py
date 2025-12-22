#!/usr/bin/env python
"""
This module defines core exceptions for the JIRA Creator application.

Plugin-specific exceptions have been moved to their respective plugin modules
and are registered via the PluginRegistry's exception registration framework.

Core exceptions defined here are used across multiple modules and are not
specific to any single plugin.
"""


class MissingConfigVariable(BaseException):
    """Represents an exception raised when a required Jira environment variable is missing."""


class AiError(BaseException):
    """This class represents a custom exception for AI-related errors."""


class JiraClientRequestError(BaseException):
    """This class represents an exception raised when there is an error in making a request to the Jira client."""


class AiProviderError(BaseException):
    """This class represents an error specific to an AI provider."""
