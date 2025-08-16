"""
Custom exceptions for the JIRA Creator application.

This module defines all custom exception classes used throughout the jira-creator
application. These exceptions provide specific error handling for different
failure scenarios in JIRA operations and AI provider interactions.

Exception Classes:
    - AiProviderError: Raised when AI provider operations fail
    - JiraRestError: Raised for JIRA REST API operation failures
    - TemplateError: Raised for template loading and processing errors
    - ConfigurationError: Raised for environment and configuration issues

These exceptions enable proper error handling and user feedback throughout
the application, allowing for graceful degradation and clear error reporting.
"""
