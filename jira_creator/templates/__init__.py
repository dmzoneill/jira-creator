"""
JIRA issue template management and loading.

This module provides functionality for loading and processing JIRA issue templates
from template files. It supports dynamic template loading with field definitions
and customizable issue creation workflows.

Key Components:
    - Template loading from .tmpl files
    - Field definition parsing and validation
    - Dynamic template field replacement
    - Support for multiple issue types (story, bug, epic, task, spike)

Main classes:
    - TemplateLoader: Core class for loading and processing issue templates

The template system allows for flexible issue creation with predefined formats
while supporting customization through field mappings and AI-enhanced descriptions.
"""
