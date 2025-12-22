"""
Custom exceptions for the JIRA Creator application.

This module defines core exception classes used throughout the jira-creator
application. Plugin-specific exceptions are now defined within their respective
plugin modules and registered via the plugin exception registry.

Core Exception Classes:
    - AiError: Raised for AI-related errors
    - AiProviderError: Raised when AI provider operations fail
    - JiraClientRequestError: Raised for JIRA REST API request failures
    - MissingConfigVariable: Raised when required configuration is missing

Plugin-specific exceptions are registered in their respective plugins via
the get_plugin_exceptions() method and accessed through the PluginRegistry.
"""
