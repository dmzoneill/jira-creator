#!/usr/bin/env python
"""
REST API client and utilities for JIRA integration.

This module provides comprehensive REST API functionality for interacting with JIRA
instances. It includes the main client for authentication and API calls, as well
as utilities for prompt management and operation handling.

Key Components:
    - Client: Main REST client for JIRA API authentication and requests
    - Prompts: AI prompt templates and management for issue enhancement
    - Operations: Specific JIRA API operations (create, update, search, etc.)

Main classes:
    - JiraClient: Primary interface for all JIRA REST API operations
    - PromptLibrary: Management of AI prompts for issue processing

The module handles authentication via JIRA Personal Access Tokens (JPAT) and provides
robust error handling and retry mechanisms for API interactions.
"""
