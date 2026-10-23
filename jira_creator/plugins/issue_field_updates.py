#!/usr/bin/env python
"""Shared Jira field updates used by more than one command plugin."""

from typing import Any, Dict


def update_issue_description(client: Any, issue_key: str, description: str) -> Dict[str, Any]:
    """Replace the description field of one issue."""
    path = f"/rest/api/2/issue/{issue_key}"
    payload = {"fields": {"description": description}}
    return client.request("PUT", path, json_data=payload)
